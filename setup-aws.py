"""Bootstrap do Lab 03. Executar no AWS CloudShell da conta indicada."""
import json
import subprocess
import sys

ACCOUNT = '844649515933'
REGION = 'us-east-1'
REPO = 'lucas-bessi7/containers-technologies'
BUCKET = ACCOUNT + '-lab03-tfstate'
ROLE = 'lab03-github-deploy'
ROLE_ARN = f'arn:aws:iam::{ACCOUNT}:role/{ROLE}'
PROVIDER = f'arn:aws:iam::{ACCOUNT}:oidc-provider/token.actions.githubusercontent.com'
EXEC_ROLE = f'arn:aws:iam::{ACCOUNT}:role/app-prod-ecs-execution'


def aws(*args, missing=None):
    p = subprocess.run(['aws', *args, '--region', REGION, '--output', 'json', '--no-cli-pager'], capture_output=True, text=True)
    if p.returncode:
        if missing and missing in p.stderr:
            return None
        sys.exit(p.stderr.strip())
    return json.loads(p.stdout) if p.stdout.strip() else {}


def stmt(actions, resources, condition=None):
    s = {'Effect': 'Allow', 'Action': actions, 'Resource': resources}
    if condition:
        s['Condition'] = condition
    return s


if aws('sts', 'get-caller-identity')['Account'] != ACCOUNT:
    sys.exit('Conta diferente da esperada. Nenhuma alteração realizada.')
if aws('iam', 'get-role', '--role-name', ROLE, missing='NoSuchEntity') is not None:
    sys.exit('A role lab03-github-deploy já existe. Pare e envie esta mensagem para revisar antes de alterar.')

region_condition = {'StringEquals': {'aws:RequestedRegion': REGION}}
lab_tag = {'StringEquals': {'aws:RequestedRegion': REGION, 'ec2:ResourceTag/Project': 'lab03'}}
policy = {'Version': '2012-10-17', 'Statement': [
    stmt(['s3:ListBucket', 's3:GetBucketLocation', 's3:GetBucketVersioning'], f'arn:aws:s3:::{BUCKET}'),
    stmt(['s3:GetObject', 's3:PutObject', 's3:DeleteObject'], f'arn:aws:s3:::{BUCKET}/*'),
    stmt(['ec2:Describe*'], '*', region_condition),
    stmt(['ec2:CreateSecurityGroup'], '*', region_condition),
    stmt(['ec2:CreateTags'], f'arn:aws:ec2:{REGION}:{ACCOUNT}:security-group/*', {'StringEquals': {'aws:RequestTag/Project': 'lab03'}}),
    stmt(['ec2:AuthorizeSecurityGroupIngress', 'ec2:AuthorizeSecurityGroupEgress', 'ec2:RevokeSecurityGroupIngress', 'ec2:RevokeSecurityGroupEgress', 'ec2:DeleteSecurityGroup', 'ec2:DeleteTags'], f'arn:aws:ec2:{REGION}:{ACCOUNT}:security-group/*', lab_tag),
    stmt(['elasticloadbalancing:Describe*'], '*', region_condition),
    stmt(['elasticloadbalancing:CreateLoadBalancer', 'elasticloadbalancing:CreateTargetGroup'], '*', {'StringEquals': {'aws:RequestedRegion': REGION, 'aws:RequestTag/Project': 'lab03'}}),
    stmt(['elasticloadbalancing:CreateListener', 'elasticloadbalancing:DeleteListener', 'elasticloadbalancing:ModifyListener', 'elasticloadbalancing:DeleteLoadBalancer', 'elasticloadbalancing:ModifyLoadBalancerAttributes', 'elasticloadbalancing:SetSecurityGroups', 'elasticloadbalancing:SetSubnets', 'elasticloadbalancing:DeleteTargetGroup', 'elasticloadbalancing:ModifyTargetGroup', 'elasticloadbalancing:ModifyTargetGroupAttributes', 'elasticloadbalancing:AddTags', 'elasticloadbalancing:RemoveTags'], [f'arn:aws:elasticloadbalancing:{REGION}:{ACCOUNT}:loadbalancer/net/app-prod-nlb/*', f'arn:aws:elasticloadbalancing:{REGION}:{ACCOUNT}:listener/net/app-prod-nlb/*/*', f'arn:aws:elasticloadbalancing:{REGION}:{ACCOUNT}:targetgroup/app-prod-tg/*']),
    stmt(['ecs:Describe*', 'ecs:List*'], '*', region_condition),
    stmt(['ecs:CreateCluster', 'ecs:RegisterTaskDefinition'], '*', {'StringEquals': {'aws:RequestedRegion': REGION, 'aws:RequestTag/Project': 'lab03'}}),
    stmt(['ecs:DeleteCluster', 'ecs:UpdateCluster', 'ecs:UpdateClusterSettings', 'ecs:CreateService', 'ecs:UpdateService', 'ecs:DeleteService', 'ecs:DeregisterTaskDefinition', 'ecs:TagResource', 'ecs:UntagResource'], [f'arn:aws:ecs:{REGION}:{ACCOUNT}:cluster/app-prod-cluster', f'arn:aws:ecs:{REGION}:{ACCOUNT}:service/app-prod-cluster/app-service', f'arn:aws:ecs:{REGION}:{ACCOUNT}:task-definition/ci-cd-app:*']),
    stmt(['logs:DescribeLogGroups'], '*', region_condition),
    stmt(['logs:CreateLogGroup', 'logs:DeleteLogGroup', 'logs:PutRetentionPolicy', 'logs:DeleteRetentionPolicy', 'logs:ListTagsLogGroup', 'logs:TagLogGroup', 'logs:UntagLogGroup', 'logs:ListTagsForResource', 'logs:TagResource', 'logs:UntagResource'], f'arn:aws:logs:{REGION}:{ACCOUNT}:log-group:/ecs/ci-cd-app*'),
    stmt(['iam:CreateRole', 'iam:GetRole', 'iam:DeleteRole', 'iam:TagRole', 'iam:UntagRole', 'iam:ListRolePolicies', 'iam:ListAttachedRolePolicies', 'iam:ListInstanceProfilesForRole', 'iam:UpdateAssumeRolePolicy'], EXEC_ROLE),
    stmt(['iam:AttachRolePolicy', 'iam:DetachRolePolicy'], EXEC_ROLE, {'ArnEquals': {'iam:PolicyARN': 'arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy'}}),
    stmt(['iam:PassRole'], EXEC_ROLE, {'StringEquals': {'iam:PassedToService': 'ecs-tasks.amazonaws.com'}}),
]}
trust = {'Version': '2012-10-17', 'Statement': [{
    'Effect': 'Allow', 'Principal': {'Federated': PROVIDER},
    'Action': 'sts:AssumeRoleWithWebIdentity',
    'Condition': {'StringEquals': {
        'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com',
        'token.actions.githubusercontent.com:sub': [f'repo:{REPO}:ref:refs/heads/main', f'repo:{REPO}:ref:refs/heads/infra']
    }}
}]}
print('Este script cria um bucket privado/versionado e uma role de deploy do lab.')
print('A role confia somente nas branches main/infra do repositório ' + REPO)
print('Pode criar recursos do lab em us-east-1 e passar somente a role de execução ECS do lab.')
print('Não inicia Fargate nem cria NLB. O deploy posterior pode gerar cobranças.')
if input('Digite CRIAR para executar: ').strip() != 'CRIAR':
    sys.exit('Cancelado. Nenhuma alteração realizada.')

buckets = aws('s3api', 'list-buckets')['Buckets']
if any(b['Name'] == BUCKET for b in buckets):
    sys.exit('Bucket já existe. Pare para revisar antes de alterar.')
aws('s3api', 'create-bucket', '--bucket', BUCKET)
aws('s3api', 'put-public-access-block', '--bucket', BUCKET, '--public-access-block-configuration', json.dumps({'BlockPublicAcls': True, 'IgnorePublicAcls': True, 'BlockPublicPolicy': True, 'RestrictPublicBuckets': True}))
aws('s3api', 'put-bucket-versioning', '--bucket', BUCKET, '--versioning-configuration', json.dumps({'Status': 'Enabled'}))
aws('s3api', 'put-bucket-encryption', '--bucket', BUCKET, '--server-side-encryption-configuration', json.dumps({'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]}))
aws('s3api', 'put-bucket-tagging', '--bucket', BUCKET, '--tagging', json.dumps({'TagSet': [{'Key': 'Project', 'Value': 'lab03'}]}))
if aws('iam', 'get-open-id-connect-provider', '--open-id-connect-provider-arn', PROVIDER, missing='NoSuchEntity') is None:
    aws('iam', 'create-open-id-connect-provider', '--url', 'https://token.actions.githubusercontent.com', '--client-id-list', 'sts.amazonaws.com')
else:
    provider = aws('iam', 'get-open-id-connect-provider', '--open-id-connect-provider-arn', PROVIDER)
    if 'sts.amazonaws.com' not in provider['ClientIDList']:
        sys.exit('Provider existente sem audiência sts.amazonaws.com; pare para revisar. Bucket já foi criado.')
# Cria roles vinculadas ao serviço somente quando ainda não existem.
for name, service in [('AWSServiceRoleForECS', 'ecs.amazonaws.com'), ('AWSServiceRoleForElasticLoadBalancing', 'elasticloadbalancing.amazonaws.com')]:
    if aws('iam', 'get-role', '--role-name', name, missing='NoSuchEntity') is None:
        aws('iam', 'create-service-linked-role', '--aws-service-name', service)
aws('iam', 'create-role', '--role-name', ROLE, '--assume-role-policy-document', json.dumps(trust), '--tags', 'Key=Project,Value=lab03')
aws('iam', 'put-role-policy', '--role-name', ROLE, '--policy-name', 'Lab03Deploy', '--policy-document', json.dumps(policy))
# Consultas finais confirmam que a configuração foi gravada.
aws('iam', 'get-role-policy', '--role-name', ROLE, '--policy-name', 'Lab03Deploy')
aws('s3api', 'get-public-access-block', '--bucket', BUCKET)
aws('s3api', 'get-bucket-versioning', '--bucket', BUCKET)
print('\nCONFIGURAÇÃO CONCLUÍDA. Configure estas Variables no GitHub:')
print('AWS_REGION=' + REGION)
print('AWS_STATE_BUCKET=' + BUCKET)
print('AWS_ROLE_ARN=' + ROLE_ARN)
