#!/usr/bin/env python3
"""
Tests pour le système de recommandation IA
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from django_app_ml.recommandation import (
    DatasetRecommendationService,
    get_ai_recommendations,
    get_recommendations_with_summary,
    RecommendationResponse
)


class TestRecommendationService(unittest.TestCase):
    """Tests pour le service de recommandation"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.mock_api_key = "test_api_key_12345"
        self.sample_audit_report = {
            "dataset_info": {
                "nom": "Test_Dataset",
                "nombre_lignes": 1000,
                "nombre_colonnes": 3
            },
            "colonnes": [
                {
                    "nom": "feature1",
                    "type": "numeric",
                    "description": "Feature numérique"
                },
                {
                    "nom": "target",
                    "type": "categorical",
                    "valeurs_uniques": ["A", "B", "C"],
                    "description": "Variable cible"
                }
            ]
        }
        
        self.sample_recommendations_response = {
            "recommendations": [
                {
                    "descriptif": "Classification multi-classes pour prédire la variable cible",
                    "type_models": ["RandomForest", "XGBoost", "LightGBM"],
                    "applications_probables": [
                        {
                            "type_application": "classification",
                            "descriptif_court": "Classification des données en 3 classes"
                        }
                    ]
                }
            ]
        }
    
    @patch('django_app_ml.recommandation.ChatOpenAI')
    def test_service_initialization(self, mock_chat_openai):
        """Test de l'initialisation du service"""
        mock_llm = Mock()
        mock_chat_openai.return_value = mock_llm
        
        service = DatasetRecommendationService(api_key=self.mock_api_key)
        
        self.assertEqual(service.api_key, self.mock_api_key)
        mock_chat_openai.assert_called_once()
    
    def test_service_initialization_no_api_key(self):
        """Test de l'initialisation sans clé API"""
        # Sauvegarder la valeur originale
        original_key = os.getenv("OPENAI_API_KEY")
        
        # Supprimer la clé API de l'environnement
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        with self.assertRaises(ValueError):
            DatasetRecommendationService()
        
        # Restaurer la valeur originale
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key
    
    @patch('django_app_ml.recommandation.ChatOpenAI')
    def test_generate_recommendations_success(self, mock_chat_openai):
        """Test de génération réussie de recommandations"""
        # Mock de la réponse de ChatGPT
        mock_response = Mock()
        mock_response.content = json.dumps(self.sample_recommendations_response)
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm
        
        service = DatasetRecommendationService(api_key=self.mock_api_key)
        recommendations = service.generate_recommendations(self.sample_audit_report)
        
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]["descriptif"], 
                        "Classification multi-classes pour prédire la variable cible")
        self.assertIn("RandomForest", recommendations[0]["type_models"])
    
    @patch('django_app_ml.recommandation.ChatOpenAI')
    def test_generate_recommendations_fallback_parsing(self, mock_chat_openai):
        """Test du fallback de parsing en cas d'erreur Pydantic"""
        # Mock d'une réponse avec du JSON valide mais format différent
        mock_response = Mock()
        mock_response.content = """
        Voici mes recommandations:
        {
            "recommendations": [
                {
                    "descriptif": "Test descriptif",
                    "type_models": ["TestModel"],
                    "applications_probables": [
                        {
                            "type_application": "test",
                            "descriptif_court": "Test app"
                        }
                    ]
                }
            ]
        }
        """
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm
        
        service = DatasetRecommendationService(api_key=self.mock_api_key)
        recommendations = service.generate_recommendations(self.sample_audit_report)
        
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]["descriptif"], "Test descriptif")
    
    def test_get_recommendations_summary(self):
        """Test de génération du résumé des recommandations"""
        service = DatasetRecommendationService(api_key=self.mock_api_key)
        
        recommendations = [
            {
                "descriptif": "Test 1",
                "type_models": ["RandomForest", "XGBoost"],
                "applications_probables": [
                    {"type_application": "classification", "descriptif_court": "Test 1"}
                ]
            },
            {
                "descriptif": "Test 2",
                "type_models": ["RandomForest", "LightGBM"],
                "applications_probables": [
                    {"type_application": "regression", "descriptif_court": "Test 2"}
                ]
            }
        ]
        
        summary = service.get_recommendations_summary(recommendations)
        
        self.assertEqual(summary["nombre_recommandations"], 2)
        self.assertEqual(summary["types_modeles_populaires"][0][0], "RandomForest")
        self.assertEqual(summary["types_modeles_populaires"][0][1], 2)
        self.assertIn("classification", [app[0] for app in summary["types_applications_populaires"]])
    
    def test_get_recommendations_summary_empty(self):
        """Test du résumé avec une liste vide"""
        service = DatasetRecommendationService(api_key=self.mock_api_key)
        
        summary = service.get_recommendations_summary([])
        
        self.assertEqual(summary["message"], "Aucune recommandation disponible")
    
    @patch('django_app_ml.recommandation.DatasetRecommendationService')
    def test_get_ai_recommendations_function(self, mock_service_class):
        """Test de la fonction utilitaire get_ai_recommendations"""
        mock_service = Mock()
        mock_service.generate_recommendations.return_value = [
            {"descriptif": "Test", "type_models": ["TestModel"], "applications_probables": []}
        ]
        mock_service_class.return_value = mock_service
        
        recommendations = get_ai_recommendations(self.sample_audit_report, self.mock_api_key)
        
        self.assertEqual(len(recommendations), 1)
        mock_service_class.assert_called_once_with(api_key=self.mock_api_key)
        mock_service.generate_recommendations.assert_called_once_with(self.sample_audit_report)
    
    @patch('django_app_ml.recommandation.DatasetRecommendationService')
    def test_get_recommendations_with_summary_function(self, mock_service_class):
        """Test de la fonction utilitaire get_recommendations_with_summary"""
        mock_service = Mock()
        mock_service.generate_recommendations.return_value = [
            {"descriptif": "Test", "type_models": ["TestModel"], "applications_probables": []}
        ]
        mock_service.get_recommendations_summary.return_value = {
            "nombre_recommandations": 1,
            "types_modeles_populaires": [["TestModel", 1]],
            "types_applications_populaires": [],
            "recommandations": []
        }
        mock_service_class.return_value = mock_service
        
        result = get_recommendations_with_summary(self.sample_audit_report, self.mock_api_key)
        
        self.assertEqual(result["nombre_recommandations"], 1)
        mock_service_class.assert_called_once_with(api_key=self.mock_api_key)
        mock_service.generate_recommendations.assert_called_once_with(self.sample_audit_report)
        mock_service.get_recommendations_summary.assert_called_once()


class TestRecommendationResponse(unittest.TestCase):
    """Tests pour la structure de réponse"""
    
    def test_recommendation_response_validation(self):
        """Test de validation de la structure de réponse"""
        valid_data = {
            "recommendations": [
                {
                    "descriptif": "Test",
                    "type_models": ["TestModel"],
                    "applications_probables": [
                        {
                            "type_application": "test",
                            "descriptif_court": "Test app"
                        }
                    ]
                }
            ]
        }
        
        response = RecommendationResponse(**valid_data)
        self.assertEqual(len(response.recommendations), 1)
        self.assertEqual(response.recommendations[0]["descriptif"], "Test")


if __name__ == "__main__":
    # Configuration pour les tests
    unittest.main(verbosity=2) 