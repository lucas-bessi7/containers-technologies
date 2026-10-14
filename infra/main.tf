data "aws_vpc" "default" {
  id = "vpc-05bd2d3e9abe1340c"
}
locals {
  subnet_ids = [
    "subnet-01b9d3f01346a116c",
    "subnet-0953bbe51186fee98",
    "subnet-06e749f8b1b4e3e50",
  ]
}
resource "aws_ecs_cluster" "this" {
  name = "app-prod-cluster"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/ci-cd-app"
  retention_in_days = 7
}
resource "aws_iam_role" "execution" {
  name = "app-prod-ecs-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}
resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
output "cluster_id" { value = aws_ecs_cluster.this.id }
output "subnet_ids" { value = local.subnet_ids }
output "execution_role_arn" { value = aws_iam_role.execution.arn }
output "log_group_name" { value = aws_cloudwatch_log_group.app.name }
output "task_sg_id" { value = aws_security_group.tasks.id }
output "target_group_arn" { value = aws_lb_target_group.this.arn }
output "nlb_dns_name" { value = "http://${aws_lb.this.dns_name}" }
