# Cyber Sentinel ML - Terraform Variables
# Configuration variables for infrastructure deployment

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "staging"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-2"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "cyber-sentinel-cluster"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.21.0/24", "10.0.22.0/24", "10.0.23.0/24"]
}

# EKS Configuration
variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "desired_capacity" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3
}

variable "min_capacity" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 2
}

variable "max_capacity" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 10
}

variable "instance_types" {
  description = "EC2 instance types for worker nodes"
  type        = list(string)
  default     = ["t3.medium", "t3.large", "t3.xlarge"]
}

# GPU Configuration
variable "gpu_desired_capacity" {
  description = "Desired number of GPU worker nodes"
  type        = number
  default     = 1
}

variable "gpu_min_capacity" {
  description = "Minimum number of GPU worker nodes"
  type        = number
  default     = 0
}

variable "gpu_max_capacity" {
  description = "Maximum number of GPU worker nodes"
  type        = number
  default     = 3
}

variable "gpu_instance_types" {
  description = "EC2 instance types for GPU worker nodes"
  type        = list(string)
  default     = ["g4dn.xlarge", "g4dn.2xlarge", "g5.xlarge"]
}

# RDS Configuration
variable "database_name" {
  description = "Name of the database"
  type        = string
  default     = "cyber_sentinel"
}

variable "database_username" {
  description = "Username for the database"
  type        = string
  default     = "cyber_user"
}

variable "database_password" {
  description = "Password for the database"
  type        = string
  sensitive   = true
  default     = ""
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.large"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS (GB)"
  type        = number
  default     = 100
}

variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

variable "backup_window" {
  description = "Preferred backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "skip_final_snapshot" {
  description = "Whether to skip final snapshot when destroying"
  type        = bool
  default     = false
}

# ElastiCache Configuration
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "redis_num_nodes" {
  description = "Number of Redis nodes"
  type        = number
  default     = 2
}

variable "redis_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "redis_auth_token" {
  description = "Authentication token for Redis"
  type        = string
  sensitive   = true
  default     = ""
}

# SSL Configuration
variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate for ALB"
  type        = string
  default     = ""
}

# Logging Configuration
variable "log_retention_days" {
  description = "Retention period for CloudWatch logs (days)"
  type        = number
  default     = 30
}

variable "audit_log_retention_days" {
  description = "Retention period for audit logs (days)"
  type        = number
  default     = 365
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Whether to enable detailed monitoring"
  type        = bool
  default     = true
}

variable "enable_cloudwatch_alarms" {
  description = "Whether to enable CloudWatch alarms"
  type        = bool
  default     = true
}

# Security Configuration
variable "enable_encryption" {
  description = "Whether to enable encryption for all resources"
  type        = bool
  default     = true
}

variable "enable_flow_logs" {
  description = "Whether to enable VPC flow logs"
  type        = bool
  default     = true
}

# Cost Optimization
variable "enable_cost_optimization" {
  description = "Whether to enable cost optimization features"
  type        = bool
  default     = true
}

variable "spot_instance_percentage" {
  description = "Percentage of spot instances in node groups"
  type        = number
  default     = 0
  
  validation {
    condition     = var.spot_instance_percentage >= 0 && var.spot_instance_percentage <= 100
    error_message = "Spot instance percentage must be between 0 and 100."
  }
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Environment-specific configurations
variable "environment_configs" {
  description = "Environment-specific configurations"
  type = object({
    development = object({
      desired_capacity    = number
      max_capacity        = number
      db_instance_class   = string
      redis_node_type     = string
      enable_monitoring   = bool
    })
    staging = object({
      desired_capacity    = number
      max_capacity        = number
      db_instance_class   = string
      redis_node_type     = string
      enable_monitoring   = bool
    })
    production = object({
      desired_capacity    = number
      max_capacity        = number
      db_instance_class   = string
      redis_node_type     = string
      enable_monitoring   = bool
    })
  })
  default = {
    development = {
      desired_capacity  = 2
      max_capacity      = 4
      db_instance_class = "db.t4g.medium"
      redis_node_type   = "cache.t4g.micro"
      enable_monitoring = false
    }
    staging = {
      desired_capacity  = 3
      max_capacity      = 6
      db_instance_class = "db.r6g.large"
      redis_node_type   = "cache.r6g.large"
      enable_monitoring = true
    }
    production = {
      desired_capacity  = 5
      max_capacity      = 20
      db_instance_class = "db.r6g.2xlarge"
      redis_node_type   = "cache.r6g.2xlarge"
      enable_monitoring = true
    }
  }
}
