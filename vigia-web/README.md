# VigiaWeb

Frontend Angular do VIGIA — autenticação JWT, listagem/detalhe de devices, stream WHEP e notificações push (Firebase).

## Development server

```bash
pnpm install
pnpm start
```

Abra `http://localhost:4200/`.

## Firebase Web Push (alertas de queda)

Push web usa o **mesmo projeto Firebase** do app Android. Sem config real, o app funciona normalmente — só não registra token FCM.

### Setup local

1. No [Firebase Console](https://console.firebase.google.com/), registre um **Web app** no projeto Vigia.
2. Em **Cloud Messaging → Web Push certificates**, gere o par VAPID e copie a **chave pública**.
3. Preencha:
   - `src/environments/environment.ts` → bloco `firebase`
   - `public/firebase-config.js` (copie de `public/firebase-config.js.example`)
4. Em **Authentication → Settings → Authorized domains**, inclua `localhost` e `vigiadeteccoes.com.br`.

Referência de placeholders: `src/environments/firebase.config.example.ts`.

### CI / produção

O workflow `web-release.yml` hidrata `public/firebase-config.js` e `environment.prod.ts` a partir do secret GitHub **`FIREBASE_WEB_CONFIG_JSON_BASE64`** (JSON em Base64):

```json
{
  "apiKey": "...",
  "authDomain": "...",
  "projectId": "...",
  "messagingSenderId": "...",
  "appId": "...",
  "vapidKey": "..."
}
```

Script: `.github/scripts/hydrate-firebase-web.sh`.

### Comportamento

- Após login, o app pede permissão de notificação e registra `PUT /users/push-token` com `platform: "web"`.
- Alertas de queda (`type: "fall"`) aparecem no **sino** da toolbar (histórico local, últimos 50) e como notificação do browser.
- Ao tocar um item (ou a notificação do sistema), navega para `/devices/:deviceId`.
- Logout remove o token FCM via `DELETE /users/push-token`.

## Building

```bash
pnpm build
```

Artefatos em `dist/vigia-web/browser`.

## Tests

```bash
pnpm test
pnpm exec ng lint
```

## Additional Resources

- [Angular CLI](https://angular.dev/tools/cli)
- Estrutura do monorepo: `docs/project-structure.md`
