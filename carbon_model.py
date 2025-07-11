#!/usr/bin/env python
# Carbon Emission Prediction Model

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.impute import SimpleImputer
import joblib
import os
import argparse

def load_data(file_path):
    """Load dataset from the given file path."""
    return pd.read_csv(file_path)

def preprocess_data(df):
    """Preprocess the data by handling missing values and encoding categorical variables."""
    # Make a copy to avoid modifying the original dataframe
    df_processed = df.copy()
    
    # Separate features and target
    X = df_processed.drop('CarbonEmission', axis=1)
    y = df_processed['CarbonEmission']
    
    # Identify categorical and numerical columns
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
    numerical_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    # Create preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols)
        ])
    
    return X, y, preprocessor, categorical_cols, numerical_cols

def train_model(X, y, preprocessor):
    """Train machine learning models and return the best one."""
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create pipelines for different models
    rf_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('imputer', SimpleImputer(strategy='median')),
        ('model', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    
    gb_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('imputer', SimpleImputer(strategy='median')),
        ('model', GradientBoostingRegressor(n_estimators=100, random_state=42))
    ])
    
    # Train models
    models = {
        'Random Forest': rf_pipeline,
        'Gradient Boosting': gb_pipeline
    }
    
    results = {}
    best_model = None
    best_score = -float('inf')
    
    for name, pipeline in models.items():
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        print(f"{name} Results:")
        print(f"MAE: {mae:.2f}")
        print(f"RMSE: {rmse:.2f}")
        print(f"R² Score: {r2:.2f}")
        print("-" * 40)
        
        results[name] = {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'model': pipeline
        }
        
        # Update best model based on R² score
        if r2 > best_score:
            best_score = r2
            best_model = {'name': name, 'pipeline': pipeline}
    
    return best_model, X_test, y_test, results

def feature_importance_analysis(model, X, categorical_cols, numerical_cols, preprocessor):
    """Analyze and visualize feature importance."""
    # For Random Forest or Gradient Boosting models
    if hasattr(model['pipeline']['model'], 'feature_importances_'):
        # Get feature names after one-hot encoding
        ohe = preprocessor.named_transformers_['cat']
        if hasattr(ohe, 'get_feature_names_out'):
            cat_features = ohe.get_feature_names_out(categorical_cols).tolist()
        else:
            cat_features = [f"{col}_{val}" for col in categorical_cols 
                           for val in ohe.categories_[categorical_cols.index(col)]]
        
        feature_names = numerical_cols + cat_features
        
        # Get feature importances
        importances = model['pipeline']['model'].feature_importances_
        
        # Create DataFrame for visualization
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        # Plot feature importances
        plt.figure(figsize=(12, 8))
        sns.barplot(x='importance', y='feature', data=importance_df.head(15))
        plt.title(f'Top 15 Feature Importances - {model["name"]}')
        plt.tight_layout()
        plt.savefig('feature_importance.png')
        print(f"Feature importance plot saved as 'feature_importance.png'")
        
        return importance_df
    else:
        print("Feature importance analysis not available for this model type.")
        return None

def save_model(model, output_path="model.pkl"):
    """Save the trained model to disk."""
    joblib.dump(model['pipeline'], output_path)
    print(f"Model saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Train a carbon emission prediction model')
    parser.add_argument('--data', type=str, required=True, help='Path to the CSV dataset')
    parser.add_argument('--output', type=str, default='model.pkl', help='Output path for the saved model')
    args = parser.parse_args()
    
    # Load data
    print("Loading data...")
    df = load_data(args.data)
    print(f"Dataset shape: {df.shape}")
    
    # Preprocess data
    print("Preprocessing data...")
    X, y, preprocessor, categorical_cols, numerical_cols = preprocess_data(df)
    
    # Train model
    print("Training models...")
    best_model, X_test, y_test, results = train_model(X, y, preprocessor)
    
    print(f"\nBest model: {best_model['name']} with R² score of {results[best_model['name']]['r2']:.2f}")
    
    # Feature importance analysis
    print("\nAnalyzing feature importance...")
    importance_df = feature_importance_analysis(best_model, X, categorical_cols, numerical_cols, preprocessor)
    if importance_df is not None:
        print("\nTop 10 most important features:")
        print(importance_df.head(10))
    
    # Save model
    save_model(best_model, args.output)

if __name__ == "__main__":
    main() 