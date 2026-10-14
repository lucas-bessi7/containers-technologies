# Lab 03 — Lucas Bessi

Arquivos preparados para o repositório lucas-bessi7/containers-technologies e imagem bessiii/containers-technologies.

## Antes de executar

1. Confirmar com o professor se a conta pessoal é aceita. O roteiro original pede AWS Academy.
2. Escolher a região. Região configurada neste pacote: us-east-1.
3. Rede confirmada na conta 844649515933: VPC vpc-05bd2d3e9abe1340c e subnets padrão de us-east-1a, us-east-1b e us-east-1c. Os IDs foram preenchidos no Terraform.
4. Criar um bucket S3 privado para o state, com versionamento e criptografia. O bucket deve estar na região escolhida.
5. Configurar uma role de deploy com autenticação OIDC do GitHub, limitada ao repositório e às branches main/infra. A configuração desta role ainda precisa ser feita na AWS. Não usar credenciais root.
6. A role de deploy precisa provisionar ECS, ELBv2, Security Groups, CloudWatch Logs, role de execução ECS e seu vínculo à policy AmazonECSTaskExecutionRolePolicy; também precisa acessar o bucket de state e passar a role de execução ao ECS.
7. Na conta pessoal nova, pode ser necessário criar as service-linked roles de ECS e ELB; conferir permissões.

## GitHub Actions: configuração

Variables:
- AWS_REGION: região selecionada.
- AWS_STATE_BUCKET: nome do bucket de state.
- AWS_ROLE_ARN: ARN da role OIDC de deploy.

Secrets:
- DOCKERHUB_USERNAME: bessiii.
- DOCKERHUB_TOKEN: token pessoal do Docker Hub com acesso de escrita; não usar a senha da conta.

A autenticação AWS utiliza OIDC: não exige AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY ou AWS_SESSION_TOKEN.

## Execução

1. Adicionar os arquivos preparados na branch infra. O workflow Deploy Infra roda nos pushes desta branch.
2. Confirmar o sucesso e os outputs. O state fica em infra-prod.tfstate.
3. Fazer PR e merge de infra para main. O workflow Deploy App roda quando há mudanças em app/ ou em seu workflow.
4. Conferir testes, build, Trivy e push. O Trivy mantém o critério do lab: bloqueia CRITICAL corrigíveis. Se bloquear, atualizar a base/dependências e corrigir; não desativar a verificação.
5. Conferir serviço app-service, cluster app-prod-cluster e três tasks saudáveis. O state da aplicação fica em app-prod.tfstate.
6. Abrir o DNS do NLB e confirmar a mensagem Container Technologies.

Os workflows também têm execução manual com operação apply/destroy. As branches não estão sendo criadas automaticamente por estes arquivos.

## Evidências reais

- GitHub: Deploy Infra concluído e etapas de validação, TFLint, tfsec, terraform-docs e apply.
- S3: os objetos infra-prod.tfstate e app-prod.tfstate; não publicar o conteúdo do state.
- AWS: cluster, NLB/listener, target group com targets saudáveis e Security Groups.
- GitHub: Building app e Deploy App concluídos, incluindo testes e Trivy.
- Docker Hub: imagem com tag v1.0.0-<7 caracteres do SHA>.
- ECS: task definition com a mesma imagem/tag, serviço com três tasks RUNNING e HEALTHY.
- CloudWatch: logs da aplicação.
- Navegador: aplicação respondendo pelo DNS do NLB.

Não utilizar os prints do professor como evidências próprias. Nenhuma evidência de execução foi gerada nesta preparação.

## Encerramento e custos

Fargate, NLB, IPv4 público, CloudWatch e S3 podem gerar cobrança; esta preparação não estima um valor e não confirma cobertura de créditos/free tier.

Após capturar evidências:
1. Executar Deploy App manualmente com operation=destroy na main e aguardar sucesso.
2. Executar Deploy Infra manualmente com operation=destroy e aguardar sucesso.
3. Conferir no console a remoção do serviço, tasks, NLB e recursos provisionados.
4. O bucket de state e a role OIDC de deploy são externos a estes states; devem ser revisados separadamente. S3 versionado pode manter versões antigas.

## Adaptações

A role LabRole foi substituída por uma role de execução ECS criada pelo Terraform. A aplicação não tem task role pois não acessa APIs AWS. O contêiner mantém o nome ci-cd-app em todos os arquivos, mesmo com a imagem containers-technologies. A task definition e o serviço são gerenciados juntos no Terraform; a action de renderização insere a tag produzida pelo build. O NLB recebe HTTP público na porta 80; as tasks aceitam a porta 8000 somente pelo Security Group do NLB. Estados de infra e app ficam separados.

Validação local: os dois testes unitários passaram; YAML, JSON e HCL foram analisados e o código foi formatado com terraform fmt. O provider foi baixado, mas terraform validate não pôde concluir porque este ambiente bloqueia sockets Unix necessários ao plugin. Build Docker, Trivy, validação completa e deploy ainda precisam rodar no GitHub Actions/AWS. O deploy e as evidências dependem da configuração das contas.

## Bootstrap no CloudShell

Enviar lab03-conta-pessoal-v2.zip ao CloudShell, extrair e executar python3 setup-aws.py. O script exibe o escopo e solicita CRIAR antes de gravar. Cria bucket privado/versionado/criptografado, provider OIDC se ausente, service-linked roles ECS/ELB se ausentes e role lab03-github-deploy com permissões limitadas ao lab. Não executa o deploy. Se houver erro, conservar a saída e revisar os recursos criados antes de repetir.
