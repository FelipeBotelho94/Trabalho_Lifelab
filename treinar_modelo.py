import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from keras import layers
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import joblib

# 1. Carregar CSV Novo
try:
    df = pd.read_csv('historico_estudo_v3.csv')
except FileNotFoundError:
    print("Erro: Rode o 'gerar_dados.py' novo primeiro!")
    exit()

# 2. Separar X (Entradas) e y (Saída)
X = df.drop('target', axis=1) # Todas as colunas menos o target
y = df['target']

# 3. Normalizar
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)
joblib.dump(scaler, 'meu_scaler_v3.pkl') # Mudamos o nome pra evitar confusão

# 4. Divisão
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)

# 5. Nova Arquitetura (Mais neurônios para processar mais dados)
model = keras.Sequential([
    layers.Input(shape=(11,)),           # Agora são 11 entradas!
    layers.Dense(64, activation='relu'), # Camada maior
    layers.Dense(32, activation='relu'),
    layers.Dense(1)
])

model.compile(optimizer='adam', loss='mean_squared_error')

print("Treinando Cérebro V3...")
model.fit(X_train, y_train, epochs=100, batch_size=32, verbose=0)

loss = model.evaluate(X_test, y_test, verbose=0)
print(f"Erro Final (MSE): {loss:.2f}")

model.save('sentinela_brain_v3.h5')
print("✅ IA V3 pronta!")