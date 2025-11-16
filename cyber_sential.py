import pandas as pd
import numpy as np
import tensorflow as tf
try:
    from tensorflow.keras import layers, models, optimizers, losses, metrics
except ImportError:
    # Fallback for different TensorFlow versions
    from keras import layers, models, optimizers, losses, metrics
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
import logging

logger = logging.getLogger(__name__)

# ---------------- TRM Model ----------------
class TinyRecursiveModel(tf.keras.Model):
    def __init__(self, input_dim, hidden_dim=128, recursive_steps=3):
        super(TinyRecursiveModel, self).__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.recursive_steps = recursive_steps
        
        # TRM Core Components
        self.feature_projection = layers.Dense(hidden_dim, activation='relu')
        self.recursive_cell = layers.GRUCell(hidden_dim)
        self.attention_gate = layers.Dense(hidden_dim, activation='sigmoid')
        
        # Multi-output heads
        self.threat_head = layers.Dense(1, activation='sigmoid')
        self.attack_type_head = layers.Dense(10, activation='softmax')  # 9 attacks + normal
        self.confidence_head = layers.Dense(1, activation='sigmoid')
        self.severity_head = layers.Dense(4, activation='softmax')  # LOW, MEDIUM, HIGH, CRITICAL
        
        logger.info(f"🧠 TRM Initialized (hidden_dim={hidden_dim}, recursive_steps={recursive_steps})")
    
    def call(self, inputs, training=False, return_all_steps=False):
        batch_size = tf.shape(inputs)[0]
        h = self.feature_projection(inputs)
        initial_state = tf.identity(h)
        
        all_states = [h]
        step_predictions = []
        state = [tf.zeros((batch_size, self.hidden_dim))]
        
        for step in range(self.recursive_steps):
            h, state = self.recursive_cell(h, state)
            attention_input = tf.concat([h, initial_state], axis=1)
            attention_weights = self.attention_gate(attention_input)
            h = h * attention_weights
            
            all_states.append(h)
            step_predictions.append(self._compute_step_predictions(h, step))
        
        final_predictions = self._compute_step_predictions(h, self.recursive_steps)
        if return_all_steps:
            return final_predictions, all_states, step_predictions
        return final_predictions
    
    def _compute_step_predictions(self, hidden_state, step):
        return {
            'threat_binary': self.threat_head(hidden_state),
            'attack_type': self.attack_type_head(hidden_state),
            'confidence': self.confidence_head(hidden_state),
            'severity': self.severity_head(hidden_state),
            'step': step
        }

# ---------------- Cyber Sentinel ----------------
class CyberSentinel:
    def __init__(self, feature_names):
        self.feature_names = feature_names
        self.trm_model = None
        self.ensemble_model = None
        self.is_trained = False
        
        self.threat_intel = {
            'severity_map': {
                'Normal': 'LOW', 'Analysis': 'MEDIUM', 'Backdoor': 'CRITICAL',
                'DoS': 'HIGH', 'Exploits': 'HIGH', 'Fuzzers': 'MEDIUM',
                'Generic': 'MEDIUM', 'Reconnaissance': 'MEDIUM', 
                'Shellcode': 'CRITICAL', 'Worms': 'CRITICAL'
            },
            'action_recommendations': {
                'Analysis': 'Enhanced monitoring and log analysis',
                'Backdoor': 'IMMEDIATE ISOLATION and forensic analysis',
                'DoS': 'Traffic filtering and rate limiting',
                'Exploits': 'Patch management and system isolation',
                'Fuzzers': 'Input validation and WAF rules',
                'Generic': 'Signature updates and system scanning',
                'Reconnaissance': 'IP blocking and alert tuning',
                'Shellcode': 'Memory analysis and process termination',
                'Worms': 'Network segmentation and antivirus updates'
            }
        }
        logger.info("🛡️ Cyber Sentinel initialized!")
    
    def train_models(self, X_train, y_train_binary, y_train_attack, epochs=30):
        logger.info("🎯 Training Cyber Sentinel models...")
        self._train_trm(X_train, y_train_binary, y_train_attack, epochs)
        self._train_ensemble(X_train, y_train_binary)
        self.is_trained = True
        logger.info("✅ All models trained successfully!")
    
    def _train_trm(self, X_train, y_train_binary, y_train_attack, epochs):
        try:
            self.trm_model = TinyRecursiveModel(input_dim=X_train.shape[1])
            # Build model manually to avoid count_params error
            self.trm_model.build(input_shape=(None, X_train.shape[1]))
            
            X_tensor = tf.convert_to_tensor(X_train, dtype=tf.float32)
            
            # Handle both pandas Series and numpy arrays
            if hasattr(y_train_binary, 'values'):
                y_binary_values = y_train_binary.values
            else:
                y_binary_values = y_train_binary
            y_binary_tensor = tf.convert_to_tensor(y_binary_values, dtype=tf.float32)
            
            attack_types = ['Normal', 'Analysis', 'Backdoor', 'DoS', 'Exploits', 
                            'Fuzzers', 'Generic', 'Reconnaissance', 'Shellcode', 'Worms']
            attack_mapping = {attack: idx for idx, attack in enumerate(attack_types)}
            
            # Handle both pandas Series and numpy arrays
            if hasattr(y_train_attack, 'values'):
                y_attack_values = y_train_attack.values
            elif hasattr(y_train_attack, 'tolist'):
                y_attack_values = y_train_attack.tolist()
            else:
                y_attack_values = list(y_train_attack)
            
            y_attack_tensor = tf.convert_to_tensor([
                attack_mapping.get(str(label), 0) for label in y_attack_values
            ], dtype=tf.int32)
            
            optimizer = optimizers.Adam(learning_rate=0.001)
            loss_fn_binary = losses.BinaryCrossentropy()
            loss_fn_attack = losses.SparseCategoricalCrossentropy()
            
            for epoch in range(epochs):
                with tf.GradientTape() as tape:
                    predictions = self.trm_model(X_tensor, training=True)
                    threat_loss = loss_fn_binary(y_binary_tensor, predictions['threat_binary'])
                    attack_loss = loss_fn_attack(y_attack_tensor, predictions['attack_type'])
                    total_loss = threat_loss + attack_loss
                
                grads = tape.gradient(total_loss, self.trm_model.trainable_variables)
                optimizer.apply_gradients(zip(grads, self.trm_model.trainable_variables))
                
                if epoch % 10 == 0:
                    try:
                        loss_val = float(total_loss.numpy())
                        logger.info(f"TRM Epoch {epoch}, Total Loss={loss_val:.4f}")
                    except:
                        logger.info(f"TRM Epoch {epoch}, Training in progress...")
        except Exception as e:
            logger.error(f"Error training TRM: {e}")
            logger.exception("TRM training traceback:")
            # Create a minimal model as fallback
            try:
                self.trm_model = TinyRecursiveModel(input_dim=len(self.feature_names))
                self.trm_model.build(input_shape=(None, len(self.feature_names)))
                logger.warning("Created fallback TRM model (untrained)")
            except Exception as fallback_error:
                logger.error(f"Failed to create fallback TRM model: {fallback_error}")
                self.trm_model = None
    
    def _train_ensemble(self, X_train, y_train_binary):
        try:
            # Handle both pandas Series and numpy arrays
            if hasattr(y_train_binary, 'values'):
                y_train_values = y_train_binary.values
            else:
                y_train_values = y_train_binary
            
            models_dict = {
                'xgb': XGBClassifier(n_estimators=100, random_state=42, verbosity=0),
                'rf': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
                'lgbm': LGBMClassifier(n_estimators=100, random_state=42, verbosity=-1)
            }
            self.ensemble_model = VotingClassifier(
                estimators=list(models_dict.items()),
                voting='soft',
                n_jobs=-1
            )
            logger.info("Training ensemble model...")
            self.ensemble_model.fit(X_train, y_train_values)
            logger.info("Ensemble model trained successfully")
        except Exception as e:
            logger.error(f"Error training ensemble: {e}")
            logger.exception("Ensemble training traceback:")
            try:
                # Fallback to simple RandomForest
                if hasattr(y_train_binary, 'values'):
                    y_train_values = y_train_binary.values
                else:
                    y_train_values = y_train_binary
                logger.warning("Falling back to simple RandomForest classifier")
                self.ensemble_model = RandomForestClassifier(n_estimators=10, random_state=42, n_jobs=-1)
                self.ensemble_model.fit(X_train, y_train_values)
                logger.info("Fallback ensemble model trained")
            except Exception as fallback_error:
                logger.error(f"Failed to train fallback ensemble model: {fallback_error}")
                self.ensemble_model = None
    
    def assess_threat(self, features, use_trm=True):
        if not self.is_trained:
            return {"error": "Model not trained"}
        
        # Convert features to proper format
        try:
            if isinstance(features, dict):
                # If features is a dict, try to extract a list/array
                if 'features' in features:
                    features = features['features']
                elif len(features) > 0:
                    # Try to convert dict values to list
                    features = list(features.values())
                else:
                    return {"error": "Invalid features format: empty dict"}
            
            # Ensure features is a list or array
            if not isinstance(features, (list, tuple, np.ndarray)):
                return {"error": f"Features must be list, tuple, or array, got {type(features)}"}
            
            # Convert to numpy array and ensure it's 1D
            features_array = np.array(features, dtype=np.float32)
            if features_array.ndim == 0:
                return {"error": "Features cannot be a scalar"}
            if features_array.ndim > 1:
                features_array = features_array.flatten()
            
            # Check feature count matches
            expected_features = len(self.feature_names)
            if len(features_array) != expected_features:
                logger.warning(f"Feature count mismatch: got {len(features_array)}, expected {expected_features}")
                # Try to pad or truncate
                if len(features_array) < expected_features:
                    features_array = np.pad(features_array, (0, expected_features - len(features_array)), mode='constant')
                else:
                    features_array = features_array[:expected_features]
        
        except Exception as e:
            logger.error(f"Error processing features: {e}")
            return {"error": f"Feature processing failed: {str(e)}"}
        
        attack_types = ['Normal', 'Analysis', 'Backdoor', 'DoS', 'Exploits', 
                        'Fuzzers', 'Generic', 'Reconnaissance', 'Shellcode', 'Worms']
        if use_trm and self.trm_model:
            return self._trm_assessment(features_array, attack_types)
        else:
            return self._ensemble_assessment(features_array, attack_types)
    
    def _trm_assessment(self, features, attack_types):
        try:
            # Ensure features is 2D for model input
            if isinstance(features, np.ndarray):
                if features.ndim == 1:
                    features_tensor = tf.convert_to_tensor([features], dtype=tf.float32)
                else:
                    features_tensor = tf.convert_to_tensor(features, dtype=tf.float32)
            else:
                features_tensor = tf.convert_to_tensor([features], dtype=tf.float32)
            
            # Get predictions
            try:
                final_pred, all_states, step_preds = self.trm_model(features_tensor, training=False, return_all_steps=True)
            except Exception as e:
                logger.error(f"TRM model prediction error: {e}")
                return {
                    'threat_detected': False,
                    'confidence': 0.0,
                    'status': 'Error',
                    'error': str(e),
                    'model_used': 'TRM'
                }
            
            # Extract predictions safely
            try:
                final_attack_idx = int(tf.argmax(final_pred['attack_type'][0]).numpy())
                if final_attack_idx >= len(attack_types):
                    final_attack_idx = 0
                final_attack = attack_types[final_attack_idx]
                
                threat_binary_val = final_pred['threat_binary'][0][0].numpy()
                threat_detected = float(threat_binary_val) > 0.5
                
                confidence_val = final_pred['confidence'][0][0].numpy()
                confidence = float(confidence_val)
            except Exception as e:
                logger.error(f"Error extracting TRM predictions: {e}")
                return {
                    'threat_detected': False,
                    'confidence': 0.0,
                    'status': 'Error',
                    'error': str(e),
                    'model_used': 'TRM'
                }
            
            if threat_detected:
                severity = self.threat_intel['severity_map'].get(final_attack, 'HIGH')
                action = self.threat_intel['action_recommendations'].get(final_attack, 'Investigate')
                return {
                    'threat_detected': True,
                    'attack_type': final_attack,
                    'confidence': confidence,
                    'severity': severity,
                    'recommended_action': action,
                    'model_used': 'TRM'
                }
            else:
                return {
                    'threat_detected': False,
                    'confidence': confidence,
                    'status': 'Normal',
                    'model_used': 'TRM'
                }
        except Exception as e:
            logger.error(f"TRM assessment error: {e}")
            logger.exception("TRM assessment traceback:")
            return {
                'threat_detected': False,
                'confidence': 0.0,
                'status': 'Error',
                'error': str(e),
                'model_used': 'TRM'
            }

    def _ensemble_assessment(self, features, attack_types):
        try:
            # Ensure features is in the right format
            if isinstance(features, np.ndarray):
                if features.ndim == 1:
                    features_array = features.reshape(1, -1)
                else:
                    features_array = features
            else:
                features_array = np.array(features, dtype=np.float32).reshape(1, -1)
            
            # Check feature count
            if features_array.shape[1] != len(self.feature_names):
                logger.warning(f"Feature count mismatch in ensemble: got {features_array.shape[1]}, expected {len(self.feature_names)}")
                # Adjust if possible
                if features_array.shape[1] < len(self.feature_names):
                    features_array = np.pad(features_array, ((0, 0), (0, len(self.feature_names) - features_array.shape[1])), mode='constant')
                else:
                    features_array = features_array[:, :len(self.feature_names)]
            
            proba = self.ensemble_model.predict_proba(features_array)[0]
            prediction = int(np.argmax(proba))
            confidence = float(np.max(proba))
            
            if prediction == 1:
                return {
                    'threat_detected': True,
                    'attack_type': 'Generic',
                    'confidence': confidence,
                    'severity': 'HIGH',
                    'recommended_action': 'General investigation required',
                    'model_used': 'Ensemble'
                }
            else:
                return {
                    'threat_detected': False,
                    'confidence': confidence,
                    'status': 'Normal',
                    'model_used': 'Ensemble'
                }
        except Exception as e:
            logger.error(f"Ensemble assessment error: {e}")
            logger.exception("Ensemble assessment traceback:")
            return {
                'threat_detected': False,
                'confidence': 0.5,
                'status': 'Unknown',
                'error': str(e),
                'model_used': 'Fallback'
            }

# ---------------- Data Loader ----------------
class UNB15DataLoader:
    def __init__(self, data_path):
        self.data_path = data_path
    
    def load_datasets(self):
        try:
            train_df = pd.read_csv(f"{self.data_path}/UNSW_NB15_training-set.csv")
            test_df = pd.read_csv(f"{self.data_path}/UNSW_NB15_testing-set.csv")
            logger.info("✅ Loaded UNSW-NB15 datasets")
            return train_df, test_df
        except Exception as e:
            logger.warning(f"Could not load datasets: {e}. Creating sample data...")
            return self._create_sample_data()
    
    def _create_sample_data(self):
        np.random.seed(42)
        n_samples = 5000
        feature_names = ['dur','proto','service','state','spkts','dpkts','sbytes','dbytes',
                         'rate','sttl','dttl','sload','dload','sloss','dloss','sinpkt','dinpkt',
                         'sjit','djit','swin','stcpb','dtcpb','dwin','tcprtt','synack','ackdat',
                         'smean','dmean','trans_depth','response_body_len','ct_srv_src','ct_state_ttl',
                         'ct_dst_ltm','ct_src_dport_ltm','ct_dst_sport_ltm','ct_dst_src_ltm','is_ftp_login',
                         'ct_ftp_cmd','ct_flw_http_mthd','ct_src_ltm','ct_srv_dst','is_sm_ips_ports']
        data = {}
        for feature in feature_names:
            if feature in ['proto', 'service', 'state']:
                data[feature] = np.random.choice(['tcp','udp','icmp'] if feature=='proto' else ['http','ftp','ssh','dns','-'] if feature=='service' else ['FIN','CON','INT','REQ'], n_samples)
            else:
                data[feature] = np.random.exponential(1.0, n_samples)
        df = pd.DataFrame(data)
        attack_types = ['Normal', 'Generic', 'Exploits', 'Fuzzers', 'DoS', 'Reconnaissance', 'Analysis', 'Backdoor', 'Shellcode', 'Worms']
        attack_probs = [0.7,0.05,0.05,0.05,0.04,0.04,0.03,0.02,0.01,0.01]
        df['attack_cat'] = np.random.choice(attack_types, n_samples, p=attack_probs)
        df['label'] = (df['attack_cat'] != 'Normal').astype(int)
        train_df = df[:4000]
        test_df = df[4000:]
        logger.info("✅ Created sample dataset")
        return train_df, test_df

# ---------------- Preprocessor ----------------
class CyberDataPreprocessor:
    def __init__(self):
        self.scaler = None
        self.label_encoders = {}
    
    def preprocess_data(self, df):
        data = df.copy()
        categorical_cols = ['proto','service','state']
        for col in categorical_cols:
            if col in data.columns:
                from sklearn.preprocessing import LabelEncoder
                self.label_encoders[col] = LabelEncoder()
                data[col] = self.label_encoders[col].fit_transform(data[col].astype(str))
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        numeric_cols = [c for c in numeric_cols if c not in ['label','attack_cat']]
        from sklearn.preprocessing import StandardScaler
        if not self.scaler:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(data[numeric_cols])
        else:
            X_scaled = self.scaler.transform(data[numeric_cols])
        y_binary = data['label']
        y_attack = data['attack_cat']
        feature_names = numeric_cols
        logger.info(f"✅ Preprocessed data: {X_scaled.shape[0]} samples, {len(feature_names)} features")
        return X_scaled, y_binary, y_attack, feature_names