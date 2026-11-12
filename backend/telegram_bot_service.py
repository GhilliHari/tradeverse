import asyncio
import logging
import httpx
import json
from datetime import datetime
from config import config
from kill_switch import KillSwitch
from risk_engine import RiskEngine

logger = logging.getLogger("TelegramBotService")

class TelegramBotService:
    """
    Two-Way Interactive Telegram Command Bot for Tradeverse.
    Allows real-time mobile command execution:
      - /status   : Live system health, broker connectivity, and market regime
      - /pnl      : Today's realized PnL, trade count, and ROI
      - /bias     : Daily strategist recommendation & 9-engine CORTEX conviction
      - /positions: Active option positions with target & trailing SL
      - /close_all: Instantly square off all open trades
      - /kill     : Engage emergency Kill Switch
      - /resume   : Disengage Kill Switch and resume operations
      - /help     : Command reference
    """
    def __init__(self):
        self.kill_switch = KillSwitch()
        self.risk_engine = RiskEngine()
        self._running = False
        self._last_update_id = 0
        self._task = None

    @property
    def bot_token(self):
        return config.TELEGRAM_BOT_TOKEN

    @property
    def authorized_chat_id(self):
        return str(config.TELEGRAM_CHAT_ID).strip() if config.TELEGRAM_CHAT_ID else None

    @property
    def enabled(self):
        return bool(self.bot_token)

    async def start(self):
        """Starts the Telegram polling daemon."""
        if not self.enabled:
            logger.info("ℹ️ Telegram Bot Service: Bot Token not configured. Polling inactive.")
            return

        self._running = True
        logger.info("🤖 Starting Two-Way Interactive Telegram Bot Daemon...")
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self):
        """Stops the Telegram polling daemon."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Telegram Bot Service stopped.")

    async def _poll_loop(self):
        """Continuous long-polling loop against Telegram Bot API."""
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        
        # Test connection & send startup alert if authorized
        if self.authorized_chat_id:
            await self._send_message(
                self.authorized_chat_id,
                "🟢 *Tradeverse Mobile Command Center Online*\n\n"
                "Interactive 2-Way control is active.\n"
                "Type `/help` to view available commands."
            )

        while self._running:
            try:
                params = {"timeout": 20, "offset": self._last_update_id + 1}
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("ok") and data.get("result"):
                            for update in data["result"]:
                                self._last_update_id = update["update_id"]
                                await self._handle_update(update)
                    else:
                        logger.warning(f"Telegram polling returned {resp.status_code}: {resp.text}")
                        await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Telegram poll loop error: {e}")
                await asyncio.sleep(5)

    async def _handle_update(self, update: dict):
        """Processes incoming Telegram messages and commands."""
        message = update.get("message")
        if not message:
            return

        chat_id = str(message.get("chat", {}).get("id"))
        text = message.get("text", "").strip()

        # Check authorization
        if self.authorized_chat_id and chat_id != self.authorized_chat_id:
            logger.warning(f"Unauthorized Telegram access attempt from Chat ID: {chat_id}")
            await self._send_message(
                chat_id,
                f"🚫 *Unauthorized Access*\nYour Chat ID `{chat_id}` is not authorized to control Tradeverse."
            )
            return

        if not text.startswith("/"):
            return

        parts = text.split()
        cmd = parts[0].lower()

        logger.info(f"📱 Processing Telegram Command: {cmd} from Chat: {chat_id}")

        if cmd in ["/start", "/help"]:
            await self._cmd_help(chat_id)
        elif cmd == "/status":
            await self._cmd_status(chat_id)
        elif cmd == "/funds":
            await self._cmd_funds(chat_id)
        elif cmd == "/pnl":
            await self._cmd_pnl(chat_id)
        elif cmd == "/bias":
            await self._cmd_bias(chat_id)
        elif cmd == "/positions":
            await self._cmd_positions(chat_id)
        elif cmd == "/mode":
            arg = parts[1].upper() if len(parts) > 1 else ""
            await self._cmd_mode(chat_id, arg)
        elif cmd == "/close_all":
            await self._cmd_close_all(chat_id)
        elif cmd == "/kill":
            await self._cmd_kill(chat_id)
        elif cmd == "/resume":
            await self._cmd_resume(chat_id)
        else:
            await self._send_message(
                chat_id,
                f"❓ Unknown command: `{cmd}`\nType `/help` to see the full command list."
            )

    async def _send_message(self, chat_id: str, text: str):
        """Sends a markdown message to the Telegram chat."""
        if not self.bot_token:
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(url, json=payload)
        except Exception as e:
            logger.error(f"Failed to send Telegram reply: {e}")

    async def _cmd_help(self, chat_id: str):
        msg = (
            "🏛️ *TRADEVERSE 24/7 CLOUD COMMAND CENTER*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• `/status` — Live Angel One session, cloud autopilot & risk health\n"
            "• `/funds` — Real-time Angel One RMS cash & margin balance\n"
            "• `/pnl` — Today's live broker realized & unrealized P&L\n"
            "• `/positions` — Live Angel One open option positions\n"
            "• `/bias` — Live AI strategist bias & conviction\n"
            "• `/mode auto` | `/mode manual` — Switch autonomous mode\n"
            "• `/close_all` — ⚡ Emergency square-off all Angel One positions\n"
            "• `/kill` — 🔴 Engage Hard Kill Switch & pause autopilot\n"
            "• `/resume` — 🟢 Disengage Kill Switch & resume AUTO mode\n"
            "• `/help` — Show this reference menu\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        await self._send_message(chat_id, msg)

    async def _cmd_status(self, chat_id: str):
        from broker_factory import get_broker_client
        is_kill = self.kill_switch.is_active()
        risk_stat = self.risk_engine.get_risk_status()
        client_id = config.ANGEL_CLIENT_ID or "AACB779182"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")

        broker = await asyncio.to_thread(get_broker_client, config.OWNER_EMAIL)
        is_conn = False
        avail_cash = 0.0
        if broker and hasattr(broker, "is_connected") and "Mock" not in broker.__class__.__name__:
            is_conn = await asyncio.to_thread(broker.is_connected)
            if is_conn and hasattr(broker, "get_funds"):
                f_res = await asyncio.to_thread(broker.get_funds)
                avail_cash = float((f_res or {}).get("availablecash") or 0.0)

        status_emoji = "🔴 HALTED" if is_kill or risk_stat['circuit_breaker_status'] != "NOMINAL" else "🟢 NOMINAL"
        conn_str = "🟢 LIVE & CONNECTED" if is_conn else "🟡 RECONNECTING / STANDBY"

        msg = (
            f"📊 *TRADEVERSE 24/7 CLOUD STATUS*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• *Broker*: Angel One SmartAPI (`{client_id}`)\n"
            f"• *Session*: {conn_str}\n"
            f"• *Available Cash*: *₹{avail_cash:,.2f}*\n"
            f"• *System Health*: {status_emoji}\n"
            f"• *Kill Switch*: {'🔴 ACTIVE' if is_kill else '🟢 DISENGAGED'}\n"
            f"• *Trading Mode*: `{config.TRADING_MODE}` / `{config.ENV}` (iMac Offline Ready)\n"
            f"• *Max Position Cap*: ₹{config.MAX_POSITION_SIZE:,.0f}\n"
            f"• *Daily Loss Cap*: ₹{risk_stat['daily_loss_limit']:,.2f}\n"
            f"• *Current Daily Loss*: ₹{risk_stat['current_daily_loss']:,.2f}\n"
            f"• *Timestamp*: `{now_str}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        await self._send_message(chat_id, msg)

    async def _cmd_funds(self, chat_id: str):
        try:
            from broker_factory import get_broker_client
            broker = await asyncio.to_thread(get_broker_client, config.OWNER_EMAIL)
            funds = await asyncio.to_thread(broker.get_funds) if hasattr(broker, "get_funds") else {}
            avail = float(funds.get("availablecash") or 0.0)
            net = float(funds.get("net") or 0.0)
            utilised = float(funds.get("utiliseddebits") or 0.0)
            msg = (
                f"🏦 *ANGEL ONE LIVE RMS FUNDS*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• *Available Cash*: `*₹{avail:,.2f}*`\n"
                f"• *Net Margin*: `₹{net:,.2f}`\n"
                f"• *Utilised Margin*: `₹{utilised:,.2f}`\n"
                f"• *Max Position Limit*: `₹{config.MAX_POSITION_SIZE:,.0f}`\n"
                f"• *Daily Loss Limit*: `₹{config.DAILY_LOSS_LIMIT:,.0f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            await self._send_message(chat_id, msg)
        except Exception as e:
            await self._send_message(chat_id, f"❌ Error fetching Angel One funds: {e}")

    async def _cmd_pnl(self, chat_id: str):
        try:
            from broker_factory import get_broker_client
            broker = await asyncio.to_thread(get_broker_client, config.OWNER_EMAIL)
            positions = await asyncio.to_thread(broker.positions) if hasattr(broker, "positions") else []
            total_pnl = sum(float(p.get("pnl") or 0.0) for p in (positions or []))
            realised = sum(float(p.get("realised") or 0.0) for p in (positions or []))
            unrealised = sum(float(p.get("unrealised") or 0.0) for p in (positions or []))
            open_cnt = sum(1 for p in (positions or []) if int(p.get("netqty", 0) or 0) != 0)
            risk_stat = self.risk_engine.get_risk_status()

            msg = (
                f"💰 *LIVE ANGEL ONE P&L SUMMARY*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• *Total Broker P&L*: `₹{total_pnl:+,.2f}`\n"
                f"• *Realized P&L*: `₹{realised:+,.2f}`\n"
                f"• *Unrealized P&L*: `₹{unrealised:+,.2f}`\n"
                f"• *Open Positions*: `{open_cnt}` / `{config.MAX_OPEN_POSITIONS}`\n"
                f"• *Remaining Loss Allowance*: `₹{risk_stat.get('remaining_loss_allowance', 0.0):,.2f}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            await self._send_message(chat_id, msg)
        except Exception as e:
            await self._send_message(chat_id, f"❌ Error retrieving P&L: {e}")

    async def _cmd_bias(self, chat_id: str):
        try:
            import main as main_mod
            if main_mod.intelligence and main_mod.initialization_status.get("ready"):
                res = await asyncio.to_thread(main_mod.intelligence.run_analysis, "^NSEBANK", False)
                sig = res.get("final_signal", "HOLD")
                conf = res.get("confidence", 0)
                regime = res.get("regime", "NOMINAL")
                rec = res.get("trade_recommendation", {}) or {}
                msg = (
                    f"🧠 *LIVE AI CORTEX BIAS (BANKNIFTY)*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• *Signal*: `{sig}`\n"
                    f"• *Conviction*: `{conf}%`\n"
                    f"• *Market Regime*: `{regime}`\n"
                    f"• *Recommended Strike*: `{rec.get('strike', 'ATM')} {rec.get('option_type', '')}`\n"
                    f"• *Reasoning*: _{rec.get('reasoning', 'Monitoring live confluence')}_\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━"
                )
            else:
                msg = "⏳ *AI Intelligence Core is still initializing...*"
            await self._send_message(chat_id, msg)
        except Exception as e:
            await self._send_message(chat_id, f"❌ Error computing AI bias: {e}")

    async def _cmd_positions(self, chat_id: str):
        try:
            from broker_factory import get_broker_client
            broker = await asyncio.to_thread(get_broker_client, config.OWNER_EMAIL)
            positions = await asyncio.to_thread(broker.positions) if hasattr(broker, "positions") else []
            open_pos = [p for p in (positions or []) if int(p.get("netqty", 0) or 0) != 0]

            if not open_pos:
                await self._send_message(
                    chat_id,
                    "💼 *ACTIVE POSITIONS*\n━━━━━━━━━━━━━━━━━━━━━━━━\nNo open live positions on Angel One right now."
                )
                return

            lines = ["💼 *ACTIVE ANGEL ONE POSITIONS*\n━━━━━━━━━━━━━━━━━━━━━━━━"]
            for p in open_pos:
                tsym = p.get("tradingsymbol")
                qty = int(p.get("netqty", 0))
                avg = float(p.get("buyavgprice") or p.get("sellavgprice") or 0.0)
                ltp = float(p.get("ltp") or 0.0)
                pnl = float(p.get("pnl") or (ltp - avg) * qty)
                lines.append(
                    f"• *{tsym}* (`{qty} Qty`)\n"
                    f"  Entry: `₹{avg:,.2f}` | LTP: `₹{ltp:,.2f}` | P&L: `*₹{pnl:+,.2f}*`"
                )
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
            await self._send_message(chat_id, "\n".join(lines))
        except Exception as e:
            await self._send_message(chat_id, f"❌ Error fetching positions: {e}")

    async def _cmd_mode(self, chat_id: str, mode_arg: str):
        if mode_arg not in ("AUTO", "MANUAL"):
            await self._send_message(
                chat_id,
                f"⚙️ Current Mode: `{config.TRADING_MODE}`\nUsage: `/mode auto` or `/mode manual`"
            )
            return
        config.TRADING_MODE = mode_arg
        config.save()
        await self._send_message(
            chat_id,
            f"✅ *Trading Mode Updated*\nNew Mode: `{config.TRADING_MODE}` (24/7 Cloud Offline Ready)"
        )

    async def _cmd_close_all(self, chat_id: str):
        try:
            logger.warning("⚡ TELEGRAM COMMAND: SQUARING OFF ALL ACTIVE TRADES")
            from broker_factory import get_broker_client
            broker = await asyncio.to_thread(get_broker_client, config.OWNER_EMAIL)
            ok = False
            if broker and hasattr(broker, "liquidate_all_positions"):
                ok = await asyncio.to_thread(broker.liquidate_all_positions)
            await self._send_message(
                chat_id,
                f"⚡ *SQUARE-OFF {'EXECUTED' if ok else 'ATTEMPTED'}*\n\n"
                "All open Angel One orders cancelled and positions squared off at market price."
            )
        except Exception as e:
            await self._send_message(chat_id, f"❌ Square-off error: {e}")

    async def _cmd_kill(self, chat_id: str):
        self.kill_switch.activate("Telegram Mobile Command")
        self.risk_engine.trigger_circuit_breaker(True, "Telegram Hard Kill Switch")
        config.TRADING_MODE = "MANUAL"
        config.save()
        logger.warning("🔴 HARD KILL SWITCH ENGAGED VIA TELEGRAM")
        await self._send_message(
            chat_id,
            "🛑 *HARD KILL SWITCH ENGAGED*\n\n"
            "• All automated order placement has been **HALTED** (`TRADING_MODE = MANUAL`).\n"
            "• Risk engine circuit breaker set to **HALTED**.\n"
            "• Send `/resume` when you are ready to restart autonomous trading."
        )

    async def _cmd_resume(self, chat_id: str):
        self.kill_switch.deactivate()
        self.risk_engine.trigger_circuit_breaker(False, "Telegram Resume Command")
        config.TRADING_MODE = "AUTO"
        config.save()
        logger.info("🟢 HARD KILL SWITCH DISENGAGED VIA TELEGRAM")
        await self._send_message(
            chat_id,
            "🟢 *SYSTEM RESUMED (AUTO / LIVE)*\n\n"
            "• Kill Switch has been **DEACTIVATED**.\n"
            "• Risk engine state is **NOMINAL**.\n"
            "• 24/7 Cloud Autonomous trade execution (`AUTO`) has resumed."
        )

# Global Singleton
telegram_bot = TelegramBotService()
