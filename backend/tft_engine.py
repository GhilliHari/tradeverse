import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TFTEngine")

class GatedResidualNetwork(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, dropout=0.1):
        super(GatedResidualNetwork, self).__init__()
        self.lin1 = nn.Linear(input_size, hidden_size)
        self.lin2 = nn.Linear(hidden_size, output_size)
        self.gate = nn.Linear(hidden_size, output_size)
        self.sigmoid = nn.Sigmoid()
        self.elu = nn.ELU()
        self.dropout = nn.Dropout(dropout)
        self.res = nn.Linear(input_size, output_size) if input_size != output_size else nn.Identity()

    def forward(self, x):
        h1 = self.elu(self.lin1(x))
        h2 = self.dropout(self.lin2(h1))
        g = self.sigmoid(self.gate(h1))
        return self.res(x) + (g * h2)

class VariableSelectionNetwork(nn.Module):
    def __init__(self, input_size, num_vars, hidden_size, dropout=0.1):
        super(VariableSelectionNetwork, self).__init__()
        self.grns = nn.ModuleList([GatedResidualNetwork(input_size, hidden_size, hidden_size, dropout) for _ in range(num_vars)])
        self.selector_grn = GatedResidualNetwork(num_vars * input_size, hidden_size, num_vars, dropout)
        self.softmax = nn.Softmax(dim=-1)

    def forward(self, x):
        # x shape: (batch, num_vars, input_size)
        var_outputs = []
        for i, grn in enumerate(self.grns):
            var_outputs.append(grn(x[:, i, :]))
        
        # Shape: (batch, num_vars, hidden_size)
        stacked_vars = torch.stack(var_outputs, dim=1)
        
        flattened_x = x.view(x.size(0), -1)
        weights = self.softmax(self.selector_grn(flattened_x)).unsqueeze(-1)
        
        selected_output = torch.sum(weights * stacked_vars, dim=1)
        return selected_output, weights

class SimplifiedTFT(nn.Module):
    def __init__(self, num_features, hidden_size, output_size=1, num_heads=4, dropout=0.1):
        super(SimplifiedTFT, self).__init__()
        self.hidden_size = hidden_size
        
        # Feature embeddings
        self.input_projections = nn.ModuleList([nn.Linear(1, hidden_size) for _ in range(num_features)])
        
        # Variable Selection
        self.vsn = VariableSelectionNetwork(hidden_size, num_features, hidden_size, dropout)
        
        # Temporal Processing (LSTM)
        self.lstm = nn.LSTM(hidden_size, hidden_size, batch_first=True)
        
        # Multi-Head Attention
        self.attention = nn.MultiheadAttention(hidden_size, num_heads, dropout=dropout, batch_first=True)
        
        # Final Output
        self.post_attention_grn = GatedResidualNetwork(hidden_size, hidden_size, hidden_size, dropout)
        self.output_layer = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        # x shape: (batch, seq_len, num_features)
        batch_size, seq_len, num_features = x.shape
        
        # Project each feature independently
        projected_features = []
        for i in range(num_features):
            projected_features.append(self.input_projections[i](x[:, :, i].unsqueeze(-1)))
        
        # Shape: (batch * seq_len, num_features, hidden_size)
        combined_features = torch.stack(projected_features, dim=2).view(-1, num_features, self.hidden_size)
        
        # Variable Selection locally for each time step
        vsn_out, vsn_weights = self.vsn(combined_features)
        vsn_out = vsn_out.view(batch_size, seq_len, self.hidden_size)
        
        # LSTM for temporal context
        lstm_out, _ = self.lstm(vsn_out)
        
        # Attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Gate and Residual
        final_h = self.post_attention_grn(attn_out[:, -1, :]) # Take last time step
        
        return self.output_layer(final_h)

class TFTEngine:
    def __init__(self, features, seq_len=30, hidden_size=64):
        self.features = features
        self.seq_len = seq_len
        self.model = SimplifiedTFT(len(features), hidden_size)
        self.scaler = StandardScaler()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        # Dynamic paths
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(base_dir, f"tft_model_brain.pth")
        self.scaler_path = os.path.join(base_dir, f"tft_scaler.joblib")

    def prepare_sequences(self, df):
        data = self.scaler.fit_transform(df[self.features])
        targets = df['Target_Next_Day'].values
        
        X, y = [], []
        for i in range(len(data) - self.seq_len):
            X.append(data[i:i+self.seq_len])
            y.append(targets[i+self.seq_len])
            
        return torch.FloatTensor(np.array(X)).to(self.device), torch.FloatTensor(np.array(y)).unsqueeze(-1).to(self.device)

    def train(self, df, epochs=10, lr=0.001):
        X, y = self.prepare_sequences(df)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.BCEWithLogitsLoss()
        
        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            output = self.model(X)
            loss = criterion(output, y)
            loss.backward()
            optimizer.step()
            if (epoch+1) % 2 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")
        
        return loss.item()

    def predict(self, recent_df):
        self.model.eval()
        # Ensure we only use the features the model was trained on
        X_data = recent_df[self.features]
        data = self.scaler.transform(X_data)
        X = torch.FloatTensor(data).unsqueeze(0).to(self.device)
        with torch.no_grad():
            output = torch.sigmoid(self.model(X))
        return output.item()

    def save_model(self):
        torch.save(self.model.state_dict(), self.model_path)
        import joblib
        joblib.dump(self.scaler, self.scaler_path)
        logger.info(f"TFT Model and Scaler saved to {self.model_path}")

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            import joblib
            self.scaler = joblib.load(self.scaler_path)
            logger.info("TFT Model Loaded successfully.")
            return True
        return False

if __name__ == "__main__":
    from data_pipeline import DataPipeline
    from model_engine import ModelEngine
    
    dp = DataPipeline("^NSEBANK")
    if dp.run_full_pipeline():
        me = ModelEngine()
        tft = TFTEngine(me.features)
        logger.info("Starting TFT Training...")
        tft.train(dp.train_data, epochs=5)
        
        # Sample prediction
        recent = dp.test_data.iloc[-30:]
        prob = tft.predict(recent)
        logger.info(f"TFT Prediction Probability for Next Day UP: {prob:.4f}")
