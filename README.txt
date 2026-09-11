ICT - Sistema de Atendimento v3

NOVO FLUXO DO USUÁRIO
1. Escolhe Telefonia ou Informática.
2. Preenche Nome completo.
3. Preenche Identifiant.
4. Confirma.
5. O sistema gera T001... ou I001...

LOGIN INTERNO
http://localhost:5000/analista

Senhas iniciais:
Ian / ict123
Rafael / ict123
Matheus / ict123
Nicolas / ict123
Gabriel / ict123
José Otávio / ict123
Lisiane / ict123
Pedro / ict123

Administrador / admin123

ALTERE AS SENHAS INICIAIS ANTES DO USO REAL.

ADMINISTRAÇÃO
O administrador pode:
- adicionar analistas;
- alterar senha;
- ativar/desativar analistas;
- adicionar motivos de atendimento;
- ativar/desativar motivos.

O cabeçalho usa o endereço oficial do logotipo Stellantis. Caso a rede não permita acesso ao site externo, o sistema mostra automaticamente o texto STELLANTIS como fallback.

Acesso usuário: http://localhost:5000
Analistas: http://localhost:5000/analista
Dashboard: http://localhost:5000/dashboard
Histórico: http://localhost:5000/historico
Administração: http://localhost:5000/admin

Antes de uso corporativo em produção: validar HTTPS, firewall, autenticação, backup e políticas internas.


ATUALIZAÇÃO v3.1
- Correção na alteração de senha dos analistas.
- Mensagem de confirmação após alteração:
  "Senha de NOME alterada com sucesso!"
- Mensagem de erro caso o usuário não exista ou a nova senha não seja informada.


ATUALIZAÇÃO v3.2
- Validação de senha duplicada pelo Identifiant.
- Se o mesmo Identifiant já possuir uma senha com status "aguardando" no dia atual,
  o sistema não gera uma nova senha.
- É exibida a mensagem:
  "Você já possui a senha X aguardando atendimento. Não é possível retirar uma nova senha enquanto ela estiver aguardando."


ATUALIZAÇÃO v3.3
- O mesmo Identifiant pode possuir simultaneamente 1 senha aguardando de Telefonia e 1 de Informática.
- O sistema bloqueia somente uma segunda senha aguardando da mesma categoria.
- Novo campo obrigatório: Número do chamado.
- O número do chamado aparece na tela da senha, fila dos analistas, atendimento em andamento e histórico.
- Migração automática adiciona numero_chamado em bancos de versões anteriores.


ATUALIZAÇÃO v3.4
- O campo "Número do chamado" continua disponível no formulário, mas agora é opcional.
- Nome e Identifiant continuam obrigatórios.
- Quando não houver número de chamado, o registro permanece sem número e o histórico/painel exibem "-".


ATUALIZAÇÃO v3.6
- Mantidos todos os recursos da versão 3.5.
- iniciar.bat agora verifica se o Python está disponível.
- Instala automaticamente as dependências do requirements.txt.
- Abre automaticamente http://127.0.0.1:5000 no navegador.
- Mostra mensagens mais claras em caso de erro.
- O servidor continua disponível na rede pelo IP do computador, usando a porta 5000.
