// Cloudflare Pages (advanced mode). O _routes.json limita este worker a /auth:
// o resto do site continua servido como estático (com o _redirects do SPA).
//
// /auth/* é repassado ao Keycloak na VM (Traefik em services.vigiadeteccoes.com.br),
// que publica KC_HOSTNAME=https://vigiadeteccoes.com.br/auth. Assim o login fica na
// mesma origem do vigia-web.
const KEYCLOAK_ORIGIN = 'https://services.vigiadeteccoes.com.br';

function isKeycloakPath(pathname) {
  return pathname === '/auth' || pathname.startsWith('/auth/');
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!isKeycloakPath(url.pathname)) {
      return env.ASSETS.fetch(request);
    }

    const target = new URL(url.pathname + url.search, KEYCLOAK_ORIGIN);
    const init = {
      method: request.method,
      headers: request.headers,
      // Os 302 do Keycloak (login, logout) precisam chegar ao browser.
      redirect: 'manual',
    };
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      init.body = request.body;
    }
    return fetch(target, init);
  },
};
