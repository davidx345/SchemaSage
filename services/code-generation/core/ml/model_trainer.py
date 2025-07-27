"""
Model training and management for ML pipeline
"""
import asyncio
import logging
import pickle
import joblib
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.cluster import KMeans, DBSCAN
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import tensorflow as tf
from tensorflow import keras

from .base import MLModel, MLModelConfig, MLTaskType, ModelStatus, MLPrediction

logger = logging.getLogger(__name__)

class ModelTrainer:
    """Handle ML model training and management"""
    
    def __init__(self):
        self.models: Dict[str, MLModel] = {}
        self.training_data: Dict[str, pd.DataFrame] = {}
        
        # Algorithm registry
        self.algorithm_registry = {
            "random_forest": RandomForestClassifier,
            "gradient_boosting": GradientBoostingRegressor,
            "kmeans": KMeans,
            "dbscan": DBSCAN,
            "neural_network": self._create_neural_network
        }
    
    async def train_model(self, config: MLModelConfig, training_data: pd.DataFrame) -> MLModel:
        """Train a new ML model"""
        try:
            logger.info(f"Starting training for model {config.model_id}")
            
            # Create model instance
            model = MLModel(
                model_id=config.model_id,
                config=config,
                model_object=None,
                preprocessor=None,
                status=ModelStatus.TRAINING
            )
            
            self.models[config.model_id] = model
            
            # Prepare data
            X, y, preprocessor = self._prepare_training_data(training_data, config)
            
            # Train model based on algorithm
            if config.algorithm in self.algorithm_registry:
                if config.algorithm == "neural_network":
                    trained_model = await self._train_neural_network(X, y, config)
                else:
                    trained_model = self._train_sklearn_model(X, y, config)
                
                # Update model
                model.model_object = trained_model
                model.preprocessor = preprocessor
                model.training_data_size = len(training_data)
                model.status = ModelStatus.TRAINED
                
                # Calculate feature importance if available
                if hasattr(trained_model, 'feature_importances_'):
                    feature_names = config.features
                    importance_dict = dict(zip(feature_names, trained_model.feature_importances_))
                    model.feature_importance = importance_dict
                
                # Evaluate model
                performance_metrics = await self._evaluate_model(trained_model, X, y, config)
                model.performance_metrics = performance_metrics
                
                logger.info(f"Model {config.model_id} trained successfully")
                return model
            
            else:
                raise ValueError(f"Unknown algorithm: {config.algorithm}")
        
        except Exception as e:
            logger.error(f"Error training model {config.model_id}: {e}")
            if config.model_id in self.models:
                self.models[config.model_id].status = ModelStatus.ERROR
            raise
    
    def _prepare_training_data(self, data: pd.DataFrame, config: MLModelConfig) -> tuple:
        """Prepare data for training"""
        # Extract features and target
        X = data[config.features].copy()
        y = data[config.target_variable].copy() if config.target_variable in data.columns else None
        
        # Handle missing values
        X = X.fillna(X.mean() if X.select_dtypes(include=[np.number]).columns.any() else X.mode().iloc[0])
        
        # Create preprocessor based on data types
        preprocessor = {}
        
        # Handle categorical variables
        categorical_columns = X.select_dtypes(include=['object']).columns
        if len(categorical_columns) > 0:
            from sklearn.preprocessing import LabelEncoder
            for col in categorical_columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                preprocessor[f'label_encoder_{col}'] = le
        
        # Scale numerical features
        numerical_columns = X.select_dtypes(include=[np.number]).columns
        if len(numerical_columns) > 0:
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X[numerical_columns] = scaler.fit_transform(X[numerical_columns])
            preprocessor['scaler'] = scaler
        
        return X, y, preprocessor
    
    def _train_sklearn_model(self, X: pd.DataFrame, y: pd.Series, config: MLModelConfig):
        """Train scikit-learn model"""
        algorithm_class = self.algorithm_registry[config.algorithm]
        
        # Initialize model with hyperparameters
        model = algorithm_class(**config.hyperparameters)
        
        # Handle different task types
        if config.task_type in [MLTaskType.SCHEMA_CLASSIFICATION, MLTaskType.ANOMALY_DETECTION]:
            # Supervised learning
            if y is not None:
                model.fit(X, y)
            else:
                raise ValueError("Target variable required for supervised learning")
        
        elif config.task_type in [MLTaskType.SIMILARITY_ANALYSIS]:
            # Unsupervised learning
            model.fit(X)
        
        return model
    
    async def _train_neural_network(self, X: pd.DataFrame, y: pd.Series, config: MLModelConfig):
        """Train neural network model"""
        input_dim = X.shape[1]
        
        # Create model architecture
        model = self._create_neural_network(input_dim, config)
        
        # Compile model
        if config.task_type == MLTaskType.SCHEMA_CLASSIFICATION:
            model.compile(
                optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy']
            )
        else:
            model.compile(
                optimizer='adam',
                loss='mse',
                metrics=['mae']
            )
        
        # Train model
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=config.hyperparameters.get('epochs', 100),
            batch_size=config.hyperparameters.get('batch_size', 32),
            verbose=0
        )
        
        return model
    
    def _create_neural_network(self, input_dim: int, config: MLModelConfig):
        """Create neural network architecture"""
        model = keras.Sequential([
            keras.layers.Dense(
                config.hyperparameters.get('hidden_units', 64),
                activation='relu',
                input_shape=(input_dim,)
            ),
            keras.layers.Dropout(config.hyperparameters.get('dropout_rate', 0.2)),
            keras.layers.Dense(
                config.hyperparameters.get('hidden_units', 64),
                activation='relu'
            ),
            keras.layers.Dropout(config.hyperparameters.get('dropout_rate', 0.2))
        ])
        
        # Output layer based on task type
        if config.task_type == MLTaskType.SCHEMA_CLASSIFICATION:
            num_classes = config.hyperparameters.get('num_classes', 10)
            model.add(keras.layers.Dense(num_classes, activation='softmax'))
        else:
            model.add(keras.layers.Dense(1))
        
        return model
    
    async def _evaluate_model(self, model, X: pd.DataFrame, y: pd.Series, config: MLModelConfig) -> Dict[str, float]:
        """Evaluate model performance"""
        try:
            metrics = {}
            
            if config.task_type == MLTaskType.SCHEMA_CLASSIFICATION:
                # Classification metrics
                if hasattr(model, 'predict'):
                    y_pred = model.predict(X)
                    
                    if hasattr(model, 'predict_proba'):
                        # Sklearn classifier
                        metrics['accuracy'] = accuracy_score(y, y_pred)
                        metrics['precision'] = precision_score(y, y_pred, average='weighted', zero_division=0)
                        metrics['recall'] = recall_score(y, y_pred, average='weighted', zero_division=0)
                        metrics['f1_score'] = f1_score(y, y_pred, average='weighted', zero_division=0)
                    else:
                        # Neural network
                        y_pred_classes = np.argmax(y_pred, axis=1) if len(y_pred.shape) > 1 else y_pred
                        metrics['accuracy'] = accuracy_score(y, y_pred_classes)
            
            elif config.task_type == MLTaskType.PERFORMANCE_PREDICTION:
                # Regression metrics
                y_pred = model.predict(X)
                metrics['mse'] = np.mean((y - y_pred) ** 2)
                metrics['mae'] = np.mean(np.abs(y - y_pred))
                metrics['r2'] = 1 - (np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y)) ** 2))
            
            elif config.task_type == MLTaskType.ANOMALY_DETECTION:
                # Anomaly detection metrics
                if hasattr(model, 'decision_function'):
                    scores = model.decision_function(X)
                    metrics['mean_anomaly_score'] = np.mean(scores)
                    metrics['std_anomaly_score'] = np.std(scores)
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            return {}
    
    async def predict(self, model_id: str, features: Dict[str, Any]) -> MLPrediction:
        """Make prediction using trained model"""
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")
            
            model = self.models[model_id]
            if model.status != ModelStatus.TRAINED:
                raise ValueError(f"Model {model_id} is not trained")
            
            # Prepare input features
            feature_df = pd.DataFrame([features])
            
            # Apply preprocessing
            if model.preprocessor:
                for step_name, preprocessor in model.preprocessor.items():
                    if step_name.startswith('label_encoder_'):
                        col_name = step_name.replace('label_encoder_', '')
                        if col_name in feature_df.columns:
                            feature_df[col_name] = preprocessor.transform(feature_df[col_name].astype(str))
                    elif step_name == 'scaler':
                        numerical_cols = feature_df.select_dtypes(include=[np.number]).columns
                        feature_df[numerical_cols] = preprocessor.transform(feature_df[numerical_cols])
            
            # Make prediction
            prediction = model.model_object.predict(feature_df)
            
            # Calculate confidence if available
            confidence = 0.5  # Default confidence
            if hasattr(model.model_object, 'predict_proba'):
                proba = model.model_object.predict_proba(feature_df)
                confidence = np.max(proba)
            
            # Generate explanation
            explanation = self._generate_explanation(model, features, prediction)
            
            prediction_result = MLPrediction(
                prediction_id=f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                model_id=model_id,
                input_features=features,
                prediction=prediction[0] if hasattr(prediction, '__len__') else prediction,
                confidence=float(confidence),
                explanation=explanation
            )
            
            return prediction_result
        
        except Exception as e:
            logger.error(f"Error making prediction with model {model_id}: {e}")
            raise
    
    def _generate_explanation(self, model: MLModel, features: Dict[str, Any], prediction: Any) -> Dict[str, Any]:
        """Generate explanation for prediction"""
        explanation = {
            'model_type': model.config.algorithm,
            'task_type': model.config.task_type.value,
            'prediction_value': str(prediction)
        }
        
        # Add feature importance if available
        if model.feature_importance:
            top_features = sorted(
                model.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            explanation['top_important_features'] = top_features
        
        # Add input feature summary
        explanation['input_summary'] = {
            'num_features': len(features),
            'feature_types': {k: type(v).__name__ for k, v in features.items()}
        }
        
        return explanation
    
    async def save_model(self, model_id: str, file_path: str) -> bool:
        """Save trained model to disk"""
        try:
            if model_id not in self.models:
                return False
            
            model = self.models[model_id]
            
            # Save model object
            if hasattr(model.model_object, 'save'):
                # TensorFlow/Keras model
                model.model_object.save(f"{file_path}_model")
            else:
                # Scikit-learn model
                joblib.dump(model.model_object, f"{file_path}_model.pkl")
            
            # Save preprocessor
            if model.preprocessor:
                joblib.dump(model.preprocessor, f"{file_path}_preprocessor.pkl")
            
            # Save model metadata
            model_metadata = {
                'config': model.config.__dict__,
                'feature_importance': model.feature_importance,
                'performance_metrics': model.performance_metrics,
                'training_data_size': model.training_data_size,
                'created_at': model.created_at.isoformat(),
                'version': model.version
            }
            
            with open(f"{file_path}_metadata.json", 'w') as f:
                import json
                json.dump(model_metadata, f, default=str, indent=2)
            
            logger.info(f"Model {model_id} saved successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error saving model {model_id}: {e}")
            return False
    
    async def load_model(self, model_id: str, file_path: str) -> bool:
        """Load trained model from disk"""
        try:
            # Load model metadata
            with open(f"{file_path}_metadata.json", 'r') as f:
                import json
                metadata = json.load(f)
            
            # Load model object
            try:
                # Try TensorFlow/Keras first
                model_object = keras.models.load_model(f"{file_path}_model")
            except:
                # Fall back to scikit-learn
                model_object = joblib.load(f"{file_path}_model.pkl")
            
            # Load preprocessor
            preprocessor = None
            try:
                preprocessor = joblib.load(f"{file_path}_preprocessor.pkl")
            except:
                pass
            
            # Reconstruct model
            config = MLModelConfig(**metadata['config'])
            model = MLModel(
                model_id=model_id,
                config=config,
                model_object=model_object,
                preprocessor=preprocessor,
                feature_importance=metadata.get('feature_importance', {}),
                performance_metrics=metadata.get('performance_metrics', {}),
                training_data_size=metadata.get('training_data_size', 0),
                status=ModelStatus.TRAINED,
                version=metadata.get('version', '1.0')
            )
            
            self.models[model_id] = model
            logger.info(f"Model {model_id} loaded successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e}")
            return False
