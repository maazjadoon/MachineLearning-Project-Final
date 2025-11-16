# Cyber Sentinel ML - Enterprise Infrastructure
# Terraform configuration for AWS deployment

terraform {
  required_version = ">= 1.3.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

# Provider configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "CyberSentinelML"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Team        = "CyberSecurity"
    }
  }
}

# Random suffix for unique resource names
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# VPC Configuration
module "vpc" {
  source = "./modules/vpc"
  
  environment = var.environment
  region      = var.aws_region
  project_name = "cyber-sentinel"
  
  cidr_block           = var.vpc_cidr
  availability_zones   = var.availability_zones
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  database_subnet_cidrs = var.database_subnet_cidrs
  
  enable_nat_gateway = true
  enable_vpn_gateway = false
  
  tags = {
    Environment = var.environment
    Project     = "CyberSentinelML"
  }
}

# EKS Cluster
module "eks" {
  source = "./modules/eks"
  
  environment = var.environment
  region      = var.aws_region
  project_name = "cyber-sentinel"
  
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnet_ids
  cluster_name    = "${var.cluster_name}-${random_string.suffix.result}"
  
  kubernetes_version = var.kubernetes_version
  
  node_groups = {
    main = {
      desired_capacity = var.desired_capacity
      max_capacity     = var.max_capacity
      min_capacity     = var.min_capacity
      
      instance_types = var.instance_types
      capacity_type  = "ON_DEMAND"
      
      k8s_labels = {
        Environment = var.environment
        Project     = "CyberSentinelML"
        Role        = "worker"
      }
      
      additional_tags = {
        Environment = var.environment
        Project     = "CyberSentinelML"
      }
    }
    
    gpu = {
      desired_capacity = var.gpu_desired_capacity
      max_capacity     = var.gpu_max_capacity
      min_capacity     = var.gpu_min_capacity
      
      instance_types = var.gpu_instance_types
      capacity_type  = "ON_DEMAND"
      
      k8s_labels = {
        Environment = var.environment
        Project     = "CyberSentinelML"
        Role        = "gpu-worker"
      }
      
      taints = {
        dedicated = {
          key    = "nvidia.com/gpu"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }
      
      additional_tags = {
        Environment = var.environment
        Project     = "CyberSentinelML"
        GPU         = "true"
      }
    }
  }
  
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }
}

# RDS Database
module "rds" {
  source = "./modules/rds"
  
  environment = var.environment
  project_name = "cyber-sentinel"
  
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.database_subnet_ids
  security_group_ids  = [module.eks.cluster_security_group_id]
  
  database_name     = var.database_name
  database_username = var.database_username
  database_password = var.database_password
  
  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  storage_type      = "gp2"
  storage_encrypted = true
  
  backup_retention_period = var.backup_retention_period
  backup_window          = var.backup_window
  maintenance_window     = var.maintenance_window
  
  skip_final_snapshot = var.skip_final_snapshot
  final_snapshot_identifier = "${var.database_name}-final-${random_string.suffix.result}"
  
  tags = {
    Environment = var.environment
    Project     = "CyberSentinelML"
  }
}

# ElastiCache Redis
module "redis" {
  source = "./modules/redis"
  
  environment = var.environment
  project_name = "cyber-sentinel"
  
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnet_ids
  security_group_ids  = [module.eks.cluster_security_group_id]
  
  node_type           = var.redis_node_type
  num_cache_nodes     = var.redis_num_nodes
  engine_version      = var.redis_engine_version
  port                = 6379
  
  parameter_group_name = "default.redis7"
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.redis_auth_token
  
  tags = {
    Environment = var.environment
    Project     = "CyberSentinelML"
  }
}

# S3 Buckets
module "s3" {
  source = "./modules/s3"
  
  environment = var.environment
  project_name = "cyber-sentinel"
  
  # Models bucket
  models_bucket = {
    name_prefix = "cyber-sentinel-models"
    versioning  = true
    encryption  = true
    lifecycle_rules = [
      {
        id     = "old_models"
        enabled = true
        transitions = [
          {
            days          = 30
            storage_class = "STANDARD_IA"
          },
          {
            days          = 90
            storage_class = "GLACIER"
          },
          {
            days          = 365
            storage_class = "DEEP_ARCHIVE"
          }
        ]
      }
    ]
  }
  
  # Logs bucket
  logs_bucket = {
    name_prefix = "cyber-sentinel-logs"
    versioning  = true
    encryption  = true
    lifecycle_rules = [
      {
        id     = "log_retention"
        enabled = true
        expiration = {
          days = 90
        }
      }
    ]
  }
  
  # Backups bucket
  backups_bucket = {
    name_prefix = "cyber-sentinel-backups"
    versioning  = true
    encryption  = true
    lifecycle_rules = [
      {
        id     = "backup_retention"
        enabled = true
        transitions = [
          {
            days          = 30
            storage_class = "STANDARD_IA"
          },
          {
            days          = 90
            storage_class = "GLACIER"
          }
        ]
      }
    ]
  }
  
  tags = {
    Environment = var.environment
    Project     = "CyberSentinelML"
  }
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  
  environment = var.environment
  project_name = "cyber-sentinel"
  
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.public_subnet_ids
  security_group_ids  = [module.eks.cluster_security_group_id]
  
  certificate_arn = var.ssl_certificate_arn
  
  target_groups = {
    api = {
      name     = "cyber-sentinel-api"
      port     = 80
      protocol = "HTTP"
      health_check = {
        enabled             = true
        healthy_threshold   = 2
        interval            = 30
        matcher             = "200"
        path                = "/health"
        port                = "traffic-port"
        protocol            = "HTTP"
        timeout             = 5
        unhealthy_threshold = 2
      }
    }
    
    frontend = {
      name     = "cyber-sentinel-frontend"
      port     = 80
      protocol = "HTTP"
      health_check = {
        enabled             = true
        healthy_threshold   = 2
        interval            = 30
        matcher             = "200"
        path                = "/health"
        port                = "traffic-port"
        protocol            = "HTTP"
        timeout             = 5
        unhealthy_threshold = 2
      }
    }
  }
  
  https_listeners = {
    main = {
      port               = 443
      protocol           = "HTTPS"
      certificate_arn    = var.ssl_certificate_arn
      target_group_index = "api"
      
      rules = {
        api = {
          priority = 100
          actions = [{
            type               = "forward"
            target_group_index = "api"
          }]
          conditions = [{
            path_pattern = {
              values = ["/api/*"]
            }
          }]
        }
        
        frontend = {
          priority = 200
          actions = [{
            type               = "forward"
            target_group_index = "frontend"
          }]
          conditions = [{
            path_pattern = {
              values = ["/*"]
            }
          }]
        }
      }
    }
  }
  
  tags = {
    Environment = var.environment
    Project     = "CyberSentinelML"
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/eks/cyber-sentinel-${var.environment}/application"
  retention_in_days = var.log_retention_days
  
  tags = {
    Environment = var.environment
    Project     = "CyberSentinelML"
  }
}

resource "aws_cloudwatch_log_group" "audit_logs" {
  name              = "/aws/eks/cyber-sentinel-${var.environment}/audit"
  retention_in_days = var.audit_log_retention_days
  
  tags = {
    Environment = var.environment
    Project     = "CyberSentinelML"
  }
}

# SNS Topics for notifications
resource "aws_sns_topic" "alerts" {
  name = "cyber-sentinel-alerts-${var.environment}"
  
  tags = {
    Environment = var.environment
    Project     = "CyberSentinelML"
  }
}

resource "aws_sns_topic" "notifications" {
  name = "cyber-sentinel-notifications-${var.environment}"
  
  tags = {
    Environment = var.environment
    Project     = "CyberSentinelML"
  }
}

# IAM Roles for Service Accounts
module "irsa" {
  source = "./modules/irsa"
  
  environment = var.environment
  project_name = "cyber-sentinel"
  
  cluster_name = module.eks.cluster_name
  
  oidc_provider_arn = module.eks.oidc_provider_arn
  
  service_accounts = {
    threat_service = {
      namespace = "cyber-sentinel"
      service_account = "threat-service"
      
      policy_arns = [
        "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
        "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
      ]
      
      custom_policies = {
        threat_service_policy = jsonencode({
          Version = "2012-10-17"
          Statement = [
            {
              Effect = "Allow"
              Action = [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
              ]
              Resource = [
                "${module.s3.models_bucket_arn}",
                "${module.s3.models_bucket_arn}/*"
              ]
            },
            {
              Effect = "Allow"
              Action = [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
              ]
              Resource = "arn:aws:logs:*:*:*"
            }
          ]
        })
      }
    }
    
    ml_service = {
      namespace = "cyber-sentinel"
      service_account = "ml-service"
      
      policy_arns = [
        "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
      ]
      
      custom_policies = {
        ml_service_policy = jsonencode({
          Version = "2012-10-17"
          Statement = [
            {
              Effect = "Allow"
              Action = [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
              ]
              Resource = [
                "${module.s3.models_bucket_arn}",
                "${module.s3.models_bucket_arn}/*"
              ]
            },
            {
              Effect = "Allow"
              Action = [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
              ]
              Resource = "arn:aws:logs:*:*:*"
            }
          ]
        })
      }
    }
  }
}

# Outputs
output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "database_endpoint" {
  description = "RDS database endpoint"
  value       = module.rds.database_endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.redis.redis_endpoint
}

output "load_balancer_dns" {
  description = "Application Load Balancer DNS name"
  value       = module.alb.alb_dns_name
}

output "models_bucket_name" {
  description = "S3 bucket name for models"
  value       = module.s3.models_bucket_name
}

output "logs_bucket_name" {
  description = "S3 bucket name for logs"
  value       = module.s3.logs_bucket_name
}

output "s3_backups_bucket_name" {
  description = "S3 bucket name for backups"
  value       = module.s3.backups_bucket_name
}
