resource "aws_lb" "this" {
  name               = "app-prod-nlb"
  internal           = false
  load_balancer_type = "network"
  subnets            = local.subnet_ids
  security_groups    = [aws_security_group.nlb.id]
}
resource "aws_lb_target_group" "this" {
  name        = "app-prod-tg"
  port        = 8000
  protocol    = "TCP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"
  health_check {
    protocol = "HTTP"
    path     = "/"
    port     = "traffic-port"
  }
}
resource "aws_lb_listener" "this" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "TCP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}
