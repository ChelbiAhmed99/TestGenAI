import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Users, Terminal, Zap, ShieldCheck, CheckCircle2, ChevronRight, FileCode2, Code2, AlertTriangle, Layers, GitBranch } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const TABS = [
  { id: 'intro', label: 'Introduction', icon: BookOpen },
  { id: 'roles', label: 'Rôles & Permissions', icon: Users },
  { id: 'smart-gen', label: 'Smart-Generator', icon: Zap },
  { id: 'playwright', label: 'Génération Playwright', icon: Terminal },
];

export default function Documentation() {
  const [activeTab, setActiveTab] = useState('intro');
  const navigate = useNavigate();

  const renderContent = () => {
    switch (activeTab) {
      case 'intro':
        return (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <div>
              <h2 className="text-2xl font-black text-[var(--text-primary)] tracking-tight mb-4">Bienvenue sur Devoteam TestGenAI</h2>
              <p className="text-[15px] leading-relaxed text-[var(--text-secondary)]">
                La plateforme <strong>Devoteam TestGenAI</strong> est un accélérateur conçu pour transformer instantanément vos spécifications métier (User Stories, Swagger, PDF) en une suite de tests automatisés prête à l'emploi.
              </p>
              <p className="text-[15px] leading-relaxed text-[var(--text-secondary)] mt-4">
                Grâce à notre moteur basé sur l'IA (LLM Gemini Flash), vous pouvez réduire le temps d'automatisation de plusieurs jours à quelques secondes, tout en respectant les standards de l'industrie (Page Object Model, BDD).
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
              {[
                { icon: Zap, title: "100% Automatisé", desc: "De la User Story jusqu'au code Playwright exécutable." },
                { icon: ShieldCheck, title: "Self-Healing", desc: "Correction automatique des erreurs de syntaxe TypeScript." },
                { icon: Layers, title: "Traçabilité", desc: "Suivi exhaustif de bout-en-bout via notre matrice intégrée." },
                { icon: GitBranch, title: "CI/CD Ready", desc: "Export transparent vers GitLab ou GitHub Actions." },
              ].map((f, i) => (
                <div key={i} className="p-5 bg-[var(--bg-hover)] border border-[var(--border-color)] rounded-xl flex items-start gap-4">
                  <div className="p-2 bg-red-500/10 rounded-lg text-red-400"><f.icon className="w-5 h-5" /></div>
                  <div>
                    <h4 className="text-sm font-bold text-[var(--text-primary)]">{f.title}</h4>
                    <p className="text-xs font-medium text-[var(--text-muted)] mt-1">{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        );

      case 'roles':
        return (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <div>
              <h2 className="text-2xl font-black text-[var(--text-primary)] tracking-tight mb-4">Gestion des Rôles</h2>
              <p className="text-[15px] leading-relaxed text-[var(--text-secondary)]">
                L'accès à la plateforme est strictement réglementé. Selon votre profil, certaines actions peuvent être grisées ou invisibles.
              </p>
            </div>
            
            <div className="space-y-4">
              <div className="card p-6 border-l-4 border-l-red-500">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-full bg-red-500/10 flex items-center justify-center text-red-400"><ShieldCheck className="w-4 h-4" /></div>
                  <h3 className="text-lg font-bold text-[var(--text-primary)]">Profil Administrateur (Admin)</h3>
                </div>
                <p className="text-[14px] text-[var(--text-secondary)] ml-11">
                  Accès intégral à la plateforme. L'Administrateur peut configurer les paramètres de l'application et possède un accès exclusif au menu <strong>User Management</strong> pour ajouter, modifier ou supprimer des collaborateurs.
                </p>
              </div>

              <div className="card p-6 border-l-4 border-l-indigo-500">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400"><Code2 className="w-4 h-4" /></div>
                  <h3 className="text-lg font-bold text-[var(--text-primary)]">Profil Ingénieur Qualité (QA)</h3>
                </div>
                <p className="text-[14px] text-[var(--text-secondary)] ml-11">
                  Profil de production par défaut. L'ingénieur QA peut ingérer de nouvelles Requirements, utiliser le Smart-Generator, lancer les pipelines de tests automatisés et consulter les matrices de traçabilité.
                </p>
              </div>

              <div className="card p-6 border-l-4 border-l-slate-500">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-full bg-slate-500/10 flex items-center justify-center text-[var(--text-secondary)]"><Users className="w-4 h-4" /></div>
                  <h3 className="text-lg font-bold text-[var(--text-primary)]">Profil Invité (Guest)</h3>
                </div>
                <p className="text-[14px] text-[var(--text-secondary)] ml-11">
                  Accès en lecture seule. Un invité ne peut visualiser que le Dashboard de pilotage (KPIs, suivi des projets) et cette documentation. Toute action générative est bloquée.
                </p>
              </div>
            </div>
          </motion.div>
        );

      case 'smart-gen':
        return (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <div>
              <h2 className="text-2xl font-black text-[var(--text-primary)] tracking-tight mb-4">Utilisation du Smart-Generator</h2>
              <p className="text-[15px] leading-relaxed text-[var(--text-secondary)]">
                Le Smart-Generator (bouton "New Requirement") est le point d'entrée de la plateforme. Vous pouvez y soumettre du texte libre, ou idéalement, une User Story formatée.
              </p>
            </div>

            <div className="card p-6 bg-amber-500/5 border-amber-500/20">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-bold text-[var(--text-primary)]">Bonnes pratiques de syntaxe</h4>
                  <p className="text-[13px] text-[var(--text-secondary)] mt-1">
                    Pour garantir 100% de fiabilité lors de la génération du code, nous recommandons fortement l'utilisation de la syntaxe <strong>BDD (Given / When / Then)</strong>. Cela permet au modèle d'identifier clairement les préconditions, les actions et les assertions.
                  </p>
                </div>
              </div>
            </div>

            <div className="card overflow-hidden border border-[var(--border-color)]">
              <div className="bg-[var(--bg-input)] px-4 py-3 flex items-center justify-between border-b border-[var(--border-color)]">
                <div className="flex items-center gap-2">
                  <FileCode2 className="w-4 h-4 text-[var(--text-muted)]" />
                  <span className="text-[12px] font-bold text-[var(--text-secondary)] uppercase tracking-widest">Exemple de User Story Optimisée</span>
                </div>
              </div>
              <div className="p-5 overflow-x-auto text-sm font-mono leading-loose text-[var(--text-secondary)]">
                <span className="text-indigo-400 font-bold">Feature:</span> Authentification Utilisateur<br/><br/>
                <span className="text-[var(--text-muted)]">  En tant que</span> client enregistré<br/>
                <span className="text-[var(--text-muted)]">  Je veux</span> pouvoir me connecter à mon compte<br/>
                <span className="text-[var(--text-muted)]">  Afin d'</span> accéder à mon espace personnel<br/><br/>
                <span className="text-emerald-400 font-bold">  Scenario:</span> Connexion réussie avec des identifiants valides<br/>
                <span className="text-red-400 font-bold">    Given</span> l'utilisateur est sur la page de connexion "/login"<br/>
                <span className="text-red-400 font-bold">    When</span> l'utilisateur saisit l'email "test@devoteam.com"<br/>
                <span className="text-red-400 font-bold">    And</span> l'utilisateur saisit le mot de passe "SecurePass123!"<br/>
                <span className="text-red-400 font-bold">    And</span> l'utilisateur clique sur le bouton "Se Connecter"<br/>
                <span className="text-red-400 font-bold">    Then</span> l'utilisateur doit être redirigé vers le Dashboard "/dashboard"<br/>
                <span className="text-red-400 font-bold">    And</span> un message "Bienvenue" doit être affiché
              </div>
            </div>
            
            <button onClick={() => navigate('/upload')} className="px-5 py-2.5 primary-gradient rounded-xl text-sm font-bold text-[var(--text-primary)] transition-all hover:opacity-90 active:scale-[0.98] inline-flex items-center gap-2 mt-4">
              <Zap className="w-4 h-4" /> Essayer le Smart-Generator
            </button>
          </motion.div>
        );

      case 'playwright':
        return (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <div>
              <h2 className="text-2xl font-black text-[var(--text-primary)] tracking-tight mb-4">Génération Playwright & CI/CD</h2>
              <p className="text-[15px] leading-relaxed text-[var(--text-secondary)]">
                Une fois le scénario Gherkin validé dans l'éditeur, la plateforme exécute un pipeline sophistiqué pour générer votre suite de test.
              </p>
            </div>

            <div className="space-y-4 relative before:absolute before:inset-0 before:ml-[23px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-[var(--border-color)] before:to-transparent">
              {[
                { title: 'Traduction IA (Gemini Flash)', desc: 'Le modèle analyse le Gherkin et génère le script en TypeScript en appliquant le design pattern Page Object Model (POM).' },
                { title: 'Validation Self-Healing', desc: "La plateforme compile le code généré en arrière-plan (via tsc). S'il y a des erreurs de syntaxe, l'IA les auto-corrige de manière itérative jusqu'à l'obtention d'un code robuste." },
                { title: 'Création du package.json & Config', desc: 'Les fichiers de configuration (playwright.config.ts, package.json) sont créés pour rendre le projet indépendant et exécutable.' },
                { title: 'Export CI/CD', desc: 'Le projet final est zippé, ou directement poussé vers votre repository GitLab / GitHub, accompagné de son fichier .gitlab-ci.yml pour exécution.' }
              ].map((step, idx) => (
                <div key={idx} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className="flex items-center justify-center w-12 h-12 rounded-full border-4 border-[var(--bg-card)] bg-[var(--bg-hover)] text-[var(--text-secondary)] group-[.is-active]:bg-red-500/20 group-[.is-active]:text-red-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 relative z-10 font-black text-lg">
                    {idx + 1}
                  </div>
                  <div className="w-[calc(100%-4rem)] md:w-[calc(50%-3rem)] p-5 rounded-2xl bg-[var(--bg-hover)] border border-[var(--border-color)] hover:bg-[var(--bg-hover)] transition-colors">
                    <h3 className="font-bold text-[var(--text-primary)] mb-1">{step.title}</h3>
                    <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="card p-6 mt-8 flex items-center justify-between bg-gradient-to-r from-indigo-500/10 to-transparent border-indigo-500/20">
              <div>
                <h4 className="text-[15px] font-bold text-[var(--text-primary)] mb-1">Voir les résultats d'exécution</h4>
                <p className="text-sm text-[var(--text-secondary)]">Accédez à la matrice de traçabilité pour vérifier les KPI (Temps, Status) des tests.</p>
              </div>
              <button onClick={() => navigate('/execution')} className="px-5 py-2.5 bg-indigo-500 hover:bg-indigo-600 rounded-xl text-sm font-bold text-[var(--text-primary)] transition-all active:scale-[0.98]">
                Historique
              </button>
            </div>
          </motion.div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="h-[calc(100vh-120px)] flex bg-[var(--bg-card)] rounded-2xl overflow-hidden border border-[var(--border-color)] shadow-2xl">
      {/* Sidebar Navigation */}
      <div className="w-64 bg-[var(--bg-input)] border-r border-[var(--border-color)] flex flex-col hidden md:flex shrink-0">
        <div className="p-6 border-b border-[var(--border-color)]">
          <h2 className="text-sm font-black text-[var(--text-primary)] uppercase tracking-widest flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-red-500" />
            Guide Utilisateur
          </h2>
        </div>
        <div className="p-4 flex-1 space-y-1">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center justify-between p-3 rounded-xl transition-all text-sm font-bold ${
                  isActive 
                    ? 'bg-red-500/10 text-red-400 border border-red-500/20 shadow-lg shadow-red-500/5' 
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </div>
                {isActive && <ChevronRight className="w-4 h-4 opacity-50" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-8 md:p-12 relative">
        <div className="absolute top-0 right-0 w-96 h-96 bg-red-500/5 rounded-full blur-[100px] pointer-events-none" />
        <div className="max-w-3xl relative z-10">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {renderContent()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
