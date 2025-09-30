import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from django.conf import settings

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from .logging import get_logger

logger = get_logger(__name__)

# Vérification de la configuration OpenAI
if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY n'est pas configurée dans les settings Django")


# Remplacement de la dataclass Application par un modèle Pydantic
class Application(BaseModel):
    """Structure pour une application IA"""
    type_application: str = Field(
        description="Type d'application (classification, prédiction, segmentation d'image, génération d'image, etc...)"
    )
    descriptif_court: str = Field(description="Description courte de l'application")


# Remplacement de la dataclass Recommendation par un modèle Pydantic
class Recommendation(BaseModel):
    """Structure pour une recommandation IA"""
    descriptif: str = Field(
        description="Description détaillée de l'utilisation possible"
    )
    type_models: List[str] = Field(
        description="Liste des types de modèles (CNN, LLM, LightGBM, RandomForest, etc...)"
    )
    applications_probables: List[Application] = Field(
        description="Liste des applications probables"
    )


class RecommendationResponse(BaseModel):
    """Structure de réponse pour les recommandations IA"""

    recommendations: List[Dict[str, Any]] = Field(
        description="Liste des recommandations d'utilisation IA pour le dataset"
    )


class DatasetRecommendationService:
    """Service pour générer des recommandations IA basées sur l'audit d'un dataset"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le service de recommandation

        Args:
            api_key: Clé API OpenAI. Si None, utilise OPENAI_API_KEY de l'environnement
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError(
                "Clé API OpenAI requise. Définissez OPENAI_API_KEY ou passez api_key"
            )

        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.3, api_key=self.api_key)

        self.parser = PydanticOutputParser(pydantic_object=RecommendationResponse)

        # Template du prompt système
        self.system_prompt = """Tu es un expert en Intelligence Artificielle spécialisé dans l'analyse de datasets et la recommandation d'applications IA.

Ta mission est d'analyser un rapport d'audit de dataset et de proposer des utilisations possibles en IA.

Pour chaque recommandation, tu dois fournir :
1. Un descriptif détaillé de l'utilisation possible
2. Les types de modèles appropriés (CNN, LLM, LightGBM, RandomForest, etc.)
3. Les applications probables avec leur type et description courte

Sois précis, réaliste et adapté aux caractéristiques du dataset analysé."""

        # Template du prompt utilisateur
        self.user_prompt_template = """Si je te donne un parquet, tu pourrais lister les utilisations possibles à faire en IA sous la forme JSON.

Je te donne les clés que tu rempliras :
- descriptif: description détaillée de l'utilisation possible
- type_models: liste des types de modèles (CNN, LLM, LightGBM, RandomForest, etc.)
- applications_probables: liste de dictionnaires avec type_application (classification, prédiction, segmentation d'image, génération d'image, etc.) et descriptif_court de l'application

Voici le rapport d'audit du dataset en JSON :

{audit_report}

Analyse ce rapport et propose des recommandations d'utilisation IA pertinentes. 
Réponds uniquement avec un JSON valide au format suivant :
{{
    "recommendations": [
        {{
            "descriptif": "description détaillée",
            "type_models": ["modèle1", "modèle2"],
            "applications_probables": [
                {{
                    "type_application": "type d'app",
                    "descriptif_court": "description courte"
                }}
            ]
        }}
    ]
}}"""

    def generate_recommendations(
        self, audit_report: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Génère des recommandations IA basées sur le rapport d'audit

        Args:
            audit_report: Rapport d'audit du dataset au format JSON

        Returns:
            Liste des recommandations d'utilisation IA
        """
        try:
            # Préparer le prompt
            user_prompt = self.user_prompt_template.format(
                audit_report=json.dumps(audit_report, indent=2, ensure_ascii=False)
            )

            # Créer les messages
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt),
            ]

            # Appeler ChatGPT
            logger.info("Appel à ChatGPT pour générer les recommandations...")
            response = self.llm.invoke(messages)

            # Parser la réponse
            try:
                parsed_response = self.parser.parse(response.content)
                recommendations = parsed_response.recommendations
                logger.info(
                    f"Génération réussie de {len(recommendations)} recommandations"
                )
                return recommendations

            except Exception as parse_error:
                logger.error(f"Erreur lors du parsing de la réponse: {parse_error}")
                # Fallback: essayer de parser manuellement
                return self._parse_response_fallback(response.content)

        except Exception as e:
            logger.error(f"Erreur lors de la génération des recommandations: {e}")
            raise

    def _parse_response_fallback(self, content: str) -> List[Dict[str, Any]]:
        """
        Méthode de fallback pour parser la réponse si le parser Pydantic échoue

        Args:
            content: Contenu de la réponse de ChatGPT

        Returns:
            Liste des recommandations parsées
        """
        try:
            # Essayer d'extraire le JSON de la réponse
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1

            if start_idx != -1 and end_idx != 0:
                json_str = content[start_idx:end_idx]
                parsed = json.loads(json_str)
                return parsed.get("recommendations", [])
            else:
                logger.error("Impossible de trouver du JSON dans la réponse")
                return []

        except json.JSONDecodeError as e:
            logger.error(f"Erreur JSON lors du parsing de fallback: {e}")
            return []

    def get_recommendations_summary(
        self, recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Génère un résumé des recommandations

        Args:
            recommendations: Liste des recommandations

        Returns:
            Résumé des recommandations
        """
        if not recommendations:
            return {"message": "Aucune recommandation disponible"}

        # Compter les types de modèles
        model_types = {}
        application_types = {}

        for rec in recommendations:
            # Compter les types de modèles
            for model_type in rec.get("type_models", []):
                model_types[model_type] = model_types.get(model_type, 0) + 1

            # Compter les types d'applications
            for app in rec.get("applications_probables", []):
                app_type = app.get("type_application", "")
                application_types[app_type] = application_types.get(app_type, 0) + 1

        return {
            "nombre_recommandations": len(recommendations),
            "types_modeles_populaires": sorted(
                model_types.items(), key=lambda x: x[1], reverse=True
            ),
            "types_applications_populaires": sorted(
                application_types.items(), key=lambda x: x[1], reverse=True
            ),
            "recommandations": recommendations,
        }


# Fonction utilitaire pour une utilisation simple
def get_ai_recommendations(
    audit_report: Dict[str, Any], api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fonction utilitaire pour obtenir des recommandations IA

    Args:
        audit_report: Rapport d'audit du dataset
        api_key: Clé API OpenAI (optionnel, utilise settings.OPENAI_API_KEY par défaut)

    Returns:
        Liste des recommandations d'utilisation IA
    """
    service = DatasetRecommendationService(api_key=api_key or settings.OPENAI_API_KEY)
    return service.generate_recommendations(audit_report)


def get_recommendations_with_summary(
    audit_report: Dict[str, Any], api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fonction utilitaire pour obtenir des recommandations avec résumé

    Args:
        audit_report: Rapport d'audit du dataset
        api_key: Clé API OpenAI (optionnel, utilise settings.OPENAI_API_KEY par défaut)

    Returns:
        Dictionnaire contenant les recommandations et leur résumé
    """
    service = DatasetRecommendationService(api_key=api_key or settings.OPENAI_API_KEY)
    recommendations = service.generate_recommendations(audit_report)
    return service.get_recommendations_summary(recommendations)


# Exemple d'utilisation avec les settings Django :
# 
# # Dans votre fichier .env :
# OPENAI_API_KEY=your_openai_api_key_here
# 
# # Dans votre code Django :
# from django_app_ml.recommandation import get_ai_recommendations
# 
# # Utilise automatiquement settings.OPENAI_API_KEY
# recommendations = get_ai_recommendations(audit_report)
# 
# # Ou avec une clé API spécifique :
# recommendations = get_ai_recommendations(audit_report, api_key="custom_key")
