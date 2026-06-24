# US-042 : Authentification utilisateur

## User Story

**En tant qu'** utilisateur enregistré,
**Je veux** me connecter avec mes identifiants (email et mot de passe),
**Afin de** pouvoir accéder à mon tableau de bord personnalisé.

## Critères d'acceptation

- Les identifiants valides (email + mot de passe correct) redirigent l'utilisateur vers le tableau de bord
- Les identifiants invalides (mot de passe incorrect) affichent un message d'erreur "Email ou mot de passe incorrect"
- Les champs vides affichent des erreurs de validation inline ("Ce champ est requis")
- Après 5 tentatives échouées, le compte est temporairement verrouillé pendant 15 minutes
- Le mot de passe doit contenir au minimum 8 caractères, une majuscule, un chiffre et un caractère spécial
- La session expire après 30 minutes d'inactivité
- Un lien "Mot de passe oublié" est disponible sur la page de connexion

## Informations complémentaires

- **Priorité** : Haute
- **Sprint** : Sprint 3
- **Labels** : auth, sécurité, login
- **Estimation** : 5 points

## Notes techniques

L'authentification utilise JWT. Le token est stocké en httpOnly cookie.
