## Gerenciamento de múltiplas contas (Contra Mestre)

Este recurso permite que um usuário delegue diferentes contas do Lineage 2 para outros membros da equipe (contra mestres) dentro do painel PDL, mantendo auditoria e troca rápida entre contas.

### Conceitos

- **Conta ativa**: o login do jogo atualmente selecionado na sessão. Todos os módulos sensíveis (inventário, carteira, shop, serviços e marketplace) utilizam este login para consultar personagens e executar operações no banco do jogo.
- **Contra mestre**: usuário do PDL com permissão delegada para operar uma conta que não é a sua principal. Cada delegação é registrada em `ManagedLineageAccount`.
- **Proprietário**: usuário cujo UUID está vinculado diretamente ao login do jogo (`linked_uuid`). Somente o proprietário pode criar ou remover delegações.
- **Domínio de e-mail**: quando mais de uma conta compartilha o mesmo e-mail, a primeira que confirmar o endereço se torna automaticamente a “conta mestre” desse e-mail. Todas as outras contas passam a exibir o aviso “Conta vinculada à conta mestre ...” e ficam impedidas de delegar novos contra mestres até que façam login na conta mestre.

### Fluxo

1. Acesse `Servidor > Conta > Gerenciar contas` (`/server/account/manage/`).
2. Use o seletor “Conta ativa” para escolher qual login deseja operar. O badge da conta ativa também aparece no dashboard da conta.
3. Para adicionar um contra mestre, informe:
   - Login do jogo (precisa estar vinculado ao seu usuário).
   - Username do usuário do PDL que atuará como contra mestre.
   - Observações (opcional) com as orientações desejadas.
4. Cada contra mestre pode receber acesso a múltiplas contas. O painel lista:
   - Contas que você delegou (com ação de remover acesso).
   - Contas delegadas para você (incluindo quem concedeu o acesso).

### Segurança

- Toda troca de contexto valida se o usuário possui permissão ativa na conta selecionada.
- Operações críticas (transferências, shop, serviços) continuam exigindo autenticação local (senha do PDL) e respeitam as mesmas verificações de PIN/2FA já existentes.
- Delegações podem ser revogadas a qualquer momento pelo proprietário ou por um superusuário.

### APIs

- Endpoints do dashboard podem receber o parâmetro `account_login` (query string ou corpo) para definir explicitamente a conta alvo. Sem esse parâmetro, a API usa o mesmo contexto registrado na sessão web.

