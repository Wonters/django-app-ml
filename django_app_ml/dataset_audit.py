
from typing import Dict, List, Any, Optional, Union
import json
import boto3
import numpy as np
from pathlib import Path
from smart_open import open as s_open
import pandas as pd
from .logging import get_logger
from .models import Bucket

logger = get_logger(__name__)

def convert_numpy_types(obj):
    """
    Convertit les types numpy en types Python natifs pour la sérialisation JSON
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

# Alternative avec pandas si daft n'est pas disponible
class PandasDatasetAuditor:
    """
    Alternative à DatasetAuditor utilisant pandas au lieu de daft
    """
    
    def __init__(self, bucket: Bucket):
        self.audit_results = {}
        self.bucket = bucket
    def open_dataset_from_s3(self, dataset_path: str):
        """
        Ouvre un dataset depuis S3
        """            
        session = boto3.session.Session(
            aws_access_key_id=self.bucket.access_key,
            aws_secret_access_key=self.bucket.secret_key
        )

        client = session.client("s3", endpoint_url=self.bucket.endpoint)

        # 2. Préparer les paramètres pour smart_open
        transport_params = {"client": client}

        with s_open(dataset_path, 'rb', transport_params=transport_params) as s3_file:
            if dataset_path.endswith('.parquet'):
                df = pd.read_parquet(s3_file)
            elif dataset_path.endswith('.csv'):
                df = pd.read_csv(s3_file)
            else:
                raise ValueError(f"Format de fichier non supporté: {dataset_path}")
        return df
    
    def load_dataset(self, dataset_path: str):
        """
        Charge un dataset avec pandas
        
        Args:
            dataset_path: Chemin vers le fichier dataset (parquet, csv, etc.)
            
        Returns:
            pandas.DataFrame: Dataset chargé
        """
        try:
            # Si c'est un chemin S3, utiliser open_dataset_from_s3
            if dataset_path.startswith('s3://'):
                df = self.open_dataset_from_s3(dataset_path)
                logger.info(f"Dataset chargé avec succès depuis S3: {dataset_path}")
                return df
            
            # Sinon, charger localement
            if dataset_path.endswith('.parquet'):
                df = pd.read_parquet(dataset_path)
            elif dataset_path.endswith('.csv'):
                df = pd.read_csv(dataset_path)
            else:
                raise ValueError(f"Format de fichier non supporté: {dataset_path}")
            
            logger.info(f"Dataset chargé avec succès: {dataset_path}")
            return df
        except Exception as e:
            logger.error(f"Erreur lors du chargement du dataset: {e}")
            raise
    
    def get_basic_info(self, df) -> Dict[str, Any]:
        """
        Obtient les informations de base sur le dataset
        
        Args:
            df: pandas.DataFrame
            
        Returns:
            Dict contenant les informations de base
        """
        try:
            basic_info = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "column_names": list(df.columns),
                "column_types": df.dtypes.astype(str).to_dict(),
                "memory_usage": df.memory_usage(deep=True).sum()
            }
            
            return convert_numpy_types(basic_info)
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention des informations de base: {e}")
            raise
    
    def get_missing_values(self, df) -> Dict[str, int]:
        """
        Analyse les valeurs manquantes dans le dataset
        
        Args:
            df: pandas.DataFrame
            
        Returns:
            Dict avec le nombre de valeurs manquantes par colonne
        """
        try:
            missing_counts = df.isnull().sum().to_dict()
            return convert_numpy_types(missing_counts)
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des valeurs manquantes: {e}")
            raise
    
    def get_descriptive_stats(self, df, numeric_columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calcule les statistiques descriptives pour les colonnes numériques
        
        Args:
            df: pandas.DataFrame
            numeric_columns: Liste des colonnes numériques à analyser
            
        Returns:
            Dict contenant les statistiques descriptives
        """
        try:
            if numeric_columns is None:
                numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            
            stats = {}
            for col in numeric_columns:
                if col in df.columns:
                    col_stats = df[col].describe()
                    stats[col] = {
                        "mean": col_stats['mean'],
                        "std": col_stats['std'],
                        "min": col_stats['min'],
                        "max": col_stats['max'],
                        "median": col_stats['50%']
                    }
            
            return convert_numpy_types(stats)
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques descriptives: {e}")
            raise
    
    def get_categorical_stats(self, df, categorical_columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyse les colonnes catégorielles
        
        Args:
            df: pandas.DataFrame
            categorical_columns: Liste des colonnes catégorielles à analyser
            
        Returns:
            Dict contenant les statistiques des colonnes catégorielles
        """
        try:
            if categorical_columns is None:
                categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            stats = {}
            for col in categorical_columns:
                if col in df.columns:
                    unique_count = df[col].nunique()
                    value_counts = df[col].value_counts().head(10).to_dict()
                    
                    stats[col] = {
                        "unique_count": unique_count,
                        "top_values": value_counts
                    }
            
            return convert_numpy_types(stats)
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des colonnes catégorielles: {e}")
            raise
    
    def full_audit(self, dataset_path: str, save_report: bool = True, report_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Effectue un audit complet du dataset avec pandas
        
        Args:
            dataset_path: Chemin vers le dataset
            save_report: Si True, sauvegarde le rapport
            report_path: Chemin pour sauvegarder le rapport
            
        Returns:
            Dict contenant tous les résultats de l'audit
        """
        try:
            logger.info(f"Début de l'audit du dataset avec pandas: {dataset_path}")
            
            # Charger le dataset
            df = self.load_dataset(dataset_path)
            
            # Effectuer toutes les analyses
            audit_results = {
                "dataset_path": dataset_path,
                "auditor_type": "pandas",
                "basic_info": self.get_basic_info(df),
                "missing_values": self.get_missing_values(df),
                "descriptive_stats": self.get_descriptive_stats(df),
                "categorical_stats": self.get_categorical_stats(df)
            }
            
            # Sauvegarder le rapport si demandé
            if save_report:
                if report_path is None:
                    report_path = f"audit_report_pandas_{Path(dataset_path).stem}.json"
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(audit_results, f, indent=2, default=convert_numpy_types)
                
                logger.info(f"Rapport d'audit pandas sauvegardé: {report_path}")
            
            self.audit_results = audit_results
            return audit_results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'audit complet avec pandas: {e}")
            raise
