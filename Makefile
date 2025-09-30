# Makefile pour django-app-ml

NODE_MODULES_PATH = ../../bundles/node_modules

.PHONY: help install dev build clean

help: ## Afficher l'aide
	@echo "Commandes disponibles pour django-app-ml:"
	@echo "  make install  - Installer les dépendances"
	@echo "  make dev      - Lancer le serveur de développement"
	@echo "  make build    - Compiler les assets"
	@echo "  make clean    - Nettoyer les fichiers générés"

install: ## Installer les dépendances
	@echo "📦 Installing dependencies for django-app-ml..."
	cd src && npm install
	mkdir -p $(NODE_MODULES_PATH)
	@echo "📁 Moving node_modules to $(NODE_MODULES_PATH)..."
	cd src && cp -r node_modules/* $(NODE_MODULES_PATH)/ && rm -rf node_modules
	@echo "🔗 Creating symlink to shared node_modules..."
	cd src && ln -sf ../../bundles/node_modules node_modules

dev: ## Lancer le serveur de développement
	@echo "🚀 Starting development server for django-app-ml..."
	cd src && npm run dev

build: ## Compiler les assets
	@echo "🔨 Building django-app-ml assets..."
	cd src && npm run build

clean: ## Nettoyer les fichiers générés
	@echo "🧹 Cleaning django-app-ml generated files..."
	rm -rf src/dist
	rm -rf src/node_modules