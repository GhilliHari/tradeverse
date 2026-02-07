# Tradeverse: Next-Gen AI Algorithmic Trading Platform

Tradeverse is an advanced, high-frequency algorithmic trading system powered by a hybrid AI architecture combining Large Language Models (Gemini 1.5 Flash), Deep Learning (Temporal Fusion Transformers), and Reinforcement Learning agents.

## 🚀 Key Features

### Intelligence Layer
- **Hybrid AI Engine:** Orchestrates specialized agents for Sentiment Analysis, Technical patters, and Macro-economic data.
- **TFT Deep Learning:** PyTorch-based Temporal Fusion Transformer for precise multi-horizon price forecasting.
- **RL Sniper:** Reinforcement Learning agent optimized for intraday execution and timing.
- **Swarm Consensus:** Multi-agent voting system to validate trade signals before execution.

### User Interface ("The Apple Experience")
- **Command Center Dashboard:** sleek, glassmorphic UI integrated with real-time data.
- **Confidence Gauge:** Visual representation of AI model certainty.
- **Auto-Pilot Mode:** One-click activation of full autonomous trading.
- **Live Terminal:** Real-time monitoring of P&L, open orders, and market regime.
- **Touch-Optimized:** Fully responsive design suitable for desktop and tablets.

### Architecture
- **Backend:** FastAPI (Python 3.10+) with async architecture.
- **Frontend:** React + Vite + Tailwind CSS.
- **State Management:** Redis for high-speed data caching and broker state.
- **Containerization:** Full Docker support for consistent deployment.

## 🛠️ Tech Stack

- **AI/ML:** PyTorch, Google Gemini API, Scikit-Learn, Pandas.
- **Backend:** FastAPI, Uvicorn, LangGraph.
- **Frontend:** React, Framer Motion, Recharts, Lucide Icons.
- **Broker Integration:** Angel One (SmartAPI), Zerodha (Kite Connect).

## 🏁 Getting Started

### Prerequisites
- Docker & Docker Compose
- Google Gemini API Key
- Angel One / Zerodha API Credentials

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-repo/tradeverse.git
    cd tradeverse
    ```

2.  **Configure Environment**
    Create a `.env` file in the `backend` directory:
    ```env
    # AI Keys
    GOOGLE_API_KEY=your_gemini_key
    
    # Broker Keys (Angel One)
    ANGEL_API_KEY=your_api_key
    ANGEL_CLIENT_ID=your_client_id
    ANGEL_PIN=your_pin
    ANGEL_TOTP_KEY=your_totp_secret
    
    # System
    ENV=LIVE
    REDIS_URL=redis://redis:6379/0
    ```

3.  **Run with Docker (Recommended)**
    ```bash
    docker-compose up --build
    ```
    The system will initialize:
    - Frontend: http://localhost:5173
    - Backend API: http://localhost:8000
    - Redis: Port 6379

4.  **Local Development (Manual)**
    - **Backend:**
        ```bash
        cd backend
        pip install -r requirements.txt
        uvicorn main:app --reload
        ```
    - **Frontend:**
        ```bash
        cd frontend
        npm install
        npm run dev
        ```

## 🛡️ Safety Protocols

- **Kill Switch:** Instantly liquidates all positions and stops the engine.
- **Circuit Breaker:** Auto-halts trading if daily loss exceeds defined threshold (default 2%).
- **Risk Auditor:** Independent agent that verifies every trade against risk parameters before execution.

## 📄 License

Proprietary Software. Internal Use Only.
