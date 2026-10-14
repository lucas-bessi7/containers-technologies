variable "state_bucket" { type = string }
variable "aws_region" { type = string }
variable "rendered_task_path" {
  type    = string
  default = "ecs-task-definition.json"
}
data "terraform_remote_state" "infra" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "infra-prod.tfstate"
    region = var.aws_region
  }
}
locals {
  infra = data.terraform_remote_state.infra.outputs
  task  = jsondecode(file(var.rendered_task_path))
  containers = [for c in local.task.containerDefinitions : merge(c, {
    logConfiguration = merge(c.logConfiguration, {
      options = merge(c.logConfiguration.options, {
        "awslogs-region" = var.aws_region
        "awslogs-group"  = local.infra.log_group_name
      })
    })
  })]
}
resource "aws_ecs_task_definition" "this" {
  family                   = local.task.family
  execution_role_arn       = local.infra.execution_role_arn
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = local.task.cpu
  memory                   = local.task.memory
  container_definitions    = jsonencode(local.containers)
  runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }
}
resource "aws_ecs_service" "this" {
  name                               = "app-service"
  cluster                            = local.infra.cluster_id
  task_definition                    = aws_ecs_task_definition.this.arn
  desired_count                      = 3
  launch_type                        = "FARGATE"
  wait_for_steady_state              = true
  health_check_grace_period_seconds  = 60
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
  network_configuration {
    subnets          = local.infra.subnet_ids
    security_groups  = [local.infra.task_sg_id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = local.infra.target_group_arn
    container_name   = "ci-cd-app"
    container_port   = 8000
  }
}
output "nlb_dns_name" { value = local.infra.nlb_dns_name }
output "task_definition_arn" { value = aws_ecs_task_definition.this.arn }
