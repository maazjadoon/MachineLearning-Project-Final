# Cyber Sentinel ML - Terraform Outputs
# Output values for deployed infrastructure

# EKS Cluster Outputs
output "cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint of the EKS cluster"
  value       = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  description = "Certificate authority data for the EKS cluster"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "cluster_security_group_id" {
  description = "Security group ID of the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "oidc_provider_arn" {
  description = "ARN of the OIDC provider for the cluster"
  value       = module.eks.oidc_provider_arn
}

# Node Group Outputs
output "node_groups" {
  description = "Map of node groups and their configurations"
  value       = module.eks.node_groups
}

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "database_subnet_ids" {
  description = "List of database subnet IDs"
  value       = module.vpc.database_subnet_ids
}

# Database Outputs
output "database_endpoint" {
  description = "RDS database endpoint"
  value       = module.rds.database_endpoint
}

output "database_port" {
  description = "RDS database port"
  value       = module.rds.database_port
}

output "database_arn" {
  description = "ARN of the RDS database"
  value       = module.rds.database_arn
}

output "database_security_group_id" {
  description = "Security group ID of the RDS database"
  value       = module.rds.security_group_id
}

# Redis Outputs
output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.redis.redis_endpoint
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = module.redis.redis_port
}

output "redis_security_group_id" {
  description = "Security group ID of ElastiCache Redis"
  value       = module.redis.security_group_id
}

# S3 Bucket Outputs
output "models_bucket_name" {
  description = "Name of the S3 bucket for ML models"
  value       = module.s3.models_bucket_name
}

output "models_bucket_arn" {
  description = "ARN of the S3 bucket for ML models"
  value       = module.s3.models_bucket_arn
}

output "logs_bucket_name" {
  description = "Name of the S3 bucket for logs"
  value       = module.s3.logs_bucket_name
}

output "logs_bucket_arn" {
  description = "ARN of the S3 bucket for logs"
  value       = module.s3.logs_bucket_arn
}

output "backups_bucket_name" {
  description = "Name of the S3 bucket for backups"
  value       = module.s3.backups_bucket_name
}

output "backups_bucket_arn" {
  description = "ARN of the S3 bucket for backups"
  value       = module.s3.backups_bucket_arn
}

# Load Balancer Outputs
output "load_balancer_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.alb_dns_name
}

output "load_balancer_arn" {
  description = "ARN of the Application Load Balancer"
  value       = module.alb.alb_arn
}

output "load_balancer_canonical_hosted_zone_id" {
  description = "Canonical hosted zone ID of the ALB"
  value       = module.alb.alb_canonical_hosted_zone_id
}

# Target Group Outputs
output "target_group_arns" {
  description = "ARNs of the target groups"
  value       = module.alb.target_group_arns
}

# SNS Topic Outputs
output "alerts_topic_arn" {
  description = "ARN of the alerts SNS topic"
  value       = aws_sns_topic.alerts.arn
}

output "notifications_topic_arn" {
  description = "ARN of the notifications SNS topic"
  value       = aws_sns_topic.notifications.arn
}

# CloudWatch Log Group Outputs
output "app_log_group_name" {
  description = "Name of the application log group"
  value       = aws_cloudwatch_log_group.app_logs.name
}

output "app_log_group_arn" {
  description = "ARN of the application log group"
  value       = aws_cloudwatch_log_group.app_logs.arn
}

output "audit_log_group_name" {
  description = "Name of the audit log group"
  value       = aws_cloudwatch_log_group.audit_logs.name
}

output "audit_log_group_arn" {
  description = "ARN of the audit log group"
  value       = aws_cloudwatch_log_group.audit_logs.arn
}

# IAM Role Outputs
output "service_account_roles" {
  description = "IAM roles for Kubernetes service accounts"
  value       = module.irsa.service_account_roles
  sensitive   = true
}

# Kubernetes Configuration
output "kubeconfig" {
  description = "Kubernetes configuration file content"
  value       = module.eks.kubeconfig
  sensitive   = true
}

# Additional Useful Outputs
output "region" {
  description = "AWS region"
  value       = var.aws_region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "project_name" {
  description = "Project name"
  value       = "cyber-sentinel"
}

# Cost and Usage Outputs
output "estimated_monthly_cost" {
  description = "Estimated monthly cost in USD"
  value       = {
    compute = var.environment_configs[var.environment].desired_capacity * 50
    storage = var.db_allocated_storage * 0.23
    network = 100
    total   = var.environment_configs[var.environment].desired_capacity * 50 + var.db_allocated_storage * 0.23 + 100
  }
}

# Security Outputs
output "security_group_ids" {
  description = "List of all security group IDs"
  value = {
    cluster = module.eks.cluster_security_group_id
    database = module.rds.security_group_id
    redis = module.redis.security_group_id
    alb = module.alb.alb_security_group_id
  }
}

# Monitoring Outputs
output "cloudwatch_metric_alarms" {
  description = "CloudWatch metric alarms (if enabled)"
  value       = var.enable_cloudwatch_alarms ? "Enabled" : "Disabled"
}

# Networking Outputs
output "nat_gateway_ids" {
  description = "List of NAT gateway IDs"
  value       = module.vpc.nat_gateway_ids
}

output "internet_gateway_id" {
  description = "ID of the internet gateway"
  value       = module.vpc.internet_gateway_id
}

output "route_table_ids" {
  description = "List of route table IDs"
  value       = module.vpc.route_table_ids
}

# Useful Commands Output
output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --name ${module.eks.cluster_name} --region ${var.aws_region}"
}

output "get_cluster_info" {
  description = "Command to get cluster information"
  value       = "kubectl cluster-info"
}

output "deploy_application" {
  description = "Command to deploy the application"
  value       = "kubectl apply -f ../k8s/"
}

output "monitor_deployment" {
  description = "Command to monitor deployment"
  value       = "kubectl get pods -n cyber-sentinel -w"
}
