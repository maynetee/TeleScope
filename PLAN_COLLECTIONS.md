# Plan d'Action - Fonctionnalité Collections

> **Objectif** : Transformer les collections en outil central d'organisation pour le renseignement OSINT, permettant de regrouper les channels par thème/sujet avec des vues, stats et fonctionnalités dédiées.

**Date de création** : 2025-01-16
**Statut** : Implémenté (hors options futures)

---

## Contexte

### Décisions de conception
- **Cas d'usage principal** : Regroupement par thème/sujet (Guerre Ukraine, Politique FR, Crypto scams, etc.)
- **Multi-assignation** : Un channel peut appartenir à plusieurs collections simultanément
- **Digests** : Support global + par collection au choix
- **Fonctionnalités demandées** : Alertes, exports, et autres idées utiles

### État actuel
✅ Modèle `Collection` avec relation N:M vers `Channel` (via `collection_channels`)
✅ API CRUD collections (list, create, update, delete)
✅ Filtrage messages par `channel_ids`
✅ Page collections enrichie (liste + overview + création)
✅ Sélection multi-channels + recherche + collection globale + parent + auto-assignation
✅ Vue détaillée avec messages + stats + digests + export + alertes + partage
✅ Stats par collection + overview + comparaison backend
✅ Digests par collection + filtre global
✅ Alertes par collection + centre notifications in-app

---

## Phase 1 : Fondations (Priorité Haute)

### 1.1 Amélioration du gestionnaire de collections
**Backend** : ✅ Déjà supporté (`channel_ids` dans schemas)

**Frontend** :
- [x] Ajouter un sélecteur de channels multi-select dans `CollectionManager`
- [x] Option "Tous les channels" (collection globale)
- [x] Chips/tags pour visualiser les channels sélectionnés
- [x] Recherche/filtre dans la liste des channels
- [x] Parent + auto-assignation (langues/keywords/tags) + collection par défaut

**Fichiers concernés** :
- `frontend/src/components/collections/collection-manager.tsx`
- `frontend/src/lib/api/client.ts` (si ajustements nécessaires)

### 1.2 Page de détail collection enrichie
- [x] Afficher les infos de la collection (nom, description, date création)
- [x] Feed des messages de la collection (réutiliser `MessageFeed` avec filtre)
- [x] Stats par collection + top channels + langues
- [x] Boutons d'actions : Éditer, Exporter, Supprimer, Générer digest

**Fichiers concernés** :
- `frontend/src/features/collections/collection-detail-page.tsx`

### 1.3 Assignation rapide depuis la page Channels
- [x] Dropdown/modal pour assigner un channel à une ou plusieurs collections
- [x] Indicateur visuel des collections auxquelles appartient un channel
- [x] Création rapide de collection depuis cette vue

**Fichiers concernés** :
- `frontend/src/features/channels/channels-page.tsx`
- Nouveau composant : `components/channels/channel-collection-picker.tsx`

---

## Phase 2 : Dashboard & Statistiques (Priorité Haute)

### 2.1 Vue Dashboard par collection
- [x] Sélecteur de collection dans le dashboard (dropdown ou tabs)
- [x] Widgets adaptés au scope de la collection sélectionnée
- [x] Mode "Toutes les collections" vs collection spécifique

### 2.2 Statistiques par collection
**Backend** :
- [x] Nouvel endpoint `GET /api/collections/{id}/stats`
  ```json
  {
    "message_count": 1234,
    "message_count_24h": 56,
    "message_count_7d": 320,
    "channel_count": 8,
    "top_channels": [...],
    "activity_trend": [...],
    "duplicate_rate": 0.12,
    "languages": {"ru": 45, "en": 30, "uk": 25}
  }
  ```

**Frontend** :
- [x] Carte de stats dans la liste des collections
- [x] Graphiques d'activité sur la page de détail
- [ ] Comparaison entre collections (optionnel, endpoint dispo)

**Fichiers concernés** :
- `backend/app/api/collections.py`
- `frontend/src/features/collections/collection-card.tsx`
- Nouveau : `frontend/src/components/collections/collection-stats.tsx`

### 2.3 Vue globale des collections
- [x] Page overview montrant toutes les collections avec leurs stats clés
- [ ] Tri par activité, nombre de messages, date de création
- [ ] Visualisation de la répartition (pie chart ou bar chart)

---

## Phase 3 : Digests par Collection (Priorité Moyenne)

### 3.1 Backend - Génération de digests filtrés
- [x] Modifier `generate_daily_digest` pour accepter un `collection_id` optionnel
- [x] Filtrer les messages par channels de la collection
- [x] Stocker le `collection_id` dans le modèle `Summary`

**Fichiers concernés** :
- `backend/app/services/summarizer.py`
- `backend/app/models/summary.py` (ajouter `collection_id`)
- `backend/app/schemas/summary.py`

### 3.2 Backend - Endpoints digests par collection
- [x] `POST /api/collections/{id}/digest` - Générer un digest pour la collection
- [x] `GET /api/collections/{id}/digests` - Historique des digests de la collection

### 3.3 Frontend - Interface digests par collection
- [x] Bouton "Générer digest" sur la page de détail collection
- [x] Onglet/section digests dans la collection
- [x] Filtre par collection dans la page digests globale

---

## Phase 4 : Alertes par Collection (Priorité Moyenne)

### 4.1 Backend - Modèle et API alertes
- [x] Nouveau modèle `Alert`
  ```python
  class Alert(Base):
      id: UUID
      collection_id: UUID  # FK → collections
      user_id: UUID
      name: str
      keywords: List[str]  # Mots-clés à surveiller
      entities: List[str]  # Entités spécifiques (personnes, lieux)
      min_threshold: int   # Nombre minimum de mentions
      frequency: str       # "realtime", "hourly", "daily"
      notification_channels: List[str]  # Webhooks, email, in-app
      is_active: bool
      last_triggered_at: datetime
  ```

- [x] CRUD endpoints `/api/alerts`
- [x] Service de détection en background (scheduler APScheduler)

### 4.2 Frontend - Gestion des alertes
- [x] Section alertes dans la page collection
- [x] Formulaire création/édition d'alerte
- [x] Historique des déclenchements
- [x] Centre de notifications in-app

### 4.3 Notifications
- [x] Notifications in-app (badge + dropdown)
- [ ] Webhook vers Discord/Slack (optionnel)
- [ ] Email digest des alertes (optionnel)

---

## Phase 5 : Export par Collection (Priorité Moyenne)

### 5.1 Backend - Exports filtrés
✅ Déjà supporté via `channel_ids` dans les fonctions d'export

- [x] Ajouter endpoint dédié `POST /api/collections/{id}/export`
- [x] Options : format (CSV, PDF, HTML), période, filtres additionnels
- [x] Métadonnées de la collection dans l'export

### 5.2 Frontend - Interface d'export
- [x] Bouton export sur la page collection
- [x] Modal de configuration (format, dates, options)
- [ ] Prévisualisation du nombre de messages à exporter
- [ ] Progress bar pour gros exports

**Fichiers concernés** :
- `frontend/src/features/collections/collection-detail-page.tsx`
- Nouveau : `components/collections/collection-export-dialog.tsx`

---

## Phase 6 : Fonctionnalités Avancées (Priorité Basse)

### 6.1 Collection par défaut / Auto-assignation
- [x] Définir une collection comme "par défaut" pour nouveaux channels
- [x] Règles d'auto-assignation basées sur :
  - Langue détectée du channel
  - Mots-clés dans le titre/description
  - Tags/catégories

### 6.2 Collections imbriquées (sous-collections)
- [x] Ajouter `parent_id` au modèle Collection
- [ ] Vue arborescente des collections
- [ ] Héritage des channels (sous-collection hérite des parents)

### 6.3 Recherche sémantique par collection
- [x] Filtrer la recherche vectorielle par collection
- [ ] "Questions" prédéfinies par collection (templates de recherche)
- [ ] Similarité inter-collections (trouver messages similaires dans d'autres collections)

### 6.4 Partage de collections (multi-utilisateur)
- [x] Table `collection_shares` (collection_id, user_id, permission_level)
- [x] Niveaux : viewer, editor, admin
- [ ] Invitations par email ou lien

### 6.5 Templates de collections
- [ ] Collections prédéfinies (Conflit Ukraine, Désinformation, etc.)
- [ ] Import/export de configuration de collection
- [ ] Marketplace de templates (futur)

### 6.6 Analyse comparative
- [x] Comparer l'activité de plusieurs collections (endpoint backend)
- [ ] Détecter les narratifs communs entre collections
- [ ] Timeline croisée multi-collections

---

## Modèle de données mis à jour

```sql
-- Collections (existant, à enrichir)
ALTER TABLE collections ADD COLUMN IF NOT EXISTS
    color VARCHAR(7),           -- Code couleur hex pour UI
    icon VARCHAR(50),           -- Icône (emoji ou nom d'icône)
    is_default BOOLEAN DEFAULT FALSE,
    is_global BOOLEAN DEFAULT FALSE,
    parent_id UUID REFERENCES collections(id),
    auto_assign_languages JSONB,
    auto_assign_keywords JSONB,
    auto_assign_tags JSONB;

-- Channels (enrichi)
ALTER TABLE channels ADD COLUMN IF NOT EXISTS
    tags JSONB;

-- Summaries (enrichi)
ALTER TABLE summaries ADD COLUMN IF NOT EXISTS
    collection_id UUID REFERENCES collections(id);

-- Alertes (nouveau)
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES collections(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    keywords JSONB DEFAULT '[]',
    entities JSONB DEFAULT '[]',
    min_threshold INTEGER DEFAULT 1,
    frequency VARCHAR(20) DEFAULT 'daily',
    notification_channels JSONB DEFAULT '["in_app"]',
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Historique des alertes déclenchées
CREATE TABLE alert_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID REFERENCES alerts(id) ON DELETE CASCADE,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_ids JSONB NOT NULL,  -- Liste des messages ayant déclenché
    summary TEXT
);

-- Partage de collections (futur)
CREATE TABLE collection_shares (
    collection_id UUID REFERENCES collections(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    permission VARCHAR(20) DEFAULT 'viewer',  -- viewer, editor, admin
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (collection_id, user_id)
);
```

---

## Estimation et Priorités

| Phase | Priorité | Complexité | Dépendances |
|-------|----------|------------|-------------|
| Phase 1 : Fondations | 🔴 Haute | Moyenne | Aucune |
| Phase 2 : Dashboard & Stats | 🔴 Haute | Moyenne | Phase 1 |
| Phase 3 : Digests | 🟡 Moyenne | Moyenne | Phase 1 |
| Phase 4 : Alertes | 🟡 Moyenne | Haute | Phase 1, scheduler APScheduler |
| Phase 5 : Export | 🟡 Moyenne | Faible | Phase 1 |
| Phase 6 : Avancé | 🟢 Basse | Haute | Phases 1-5 |

---

## Prochaines étapes

1. **Ajouter tri & visualisation (pie/bar)** dans l’overview collections
2. **Progress bar + prévisualisation** pour les exports volumineux
3. **Vue arborescente** pour les sous-collections
4. **Templates de collections** + invitations par email/lien

---

## Notes techniques

### Patterns à suivre
- Utiliser TanStack Query pour le state serveur
- Composants shadcn/ui pour l'UI
- i18n pour tous les textes (FR/EN)
- Tests E2E Playwright pour les parcours critiques

### Points d'attention
- Performance : lazy loading des messages dans les collections volumineuses
- UX : feedback visuel lors des opérations longues (export, génération digest)
- Sécurité : vérifier que l'utilisateur a accès à la collection sur chaque endpoint
