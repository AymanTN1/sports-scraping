terraform {
  required_version = ">= 1.6"
  required_providers {
    neon = {
      source  = "kislerdm/neon"
      version = "~> 0.6"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
    upstash = {
      source  = "upstash/upstash"
      version = "~> 1.4"
    }
  }

  # Stockage de l'état Terraform dans un backend S3 (ou Terraform Cloud)
  # Décommentez si vous utilisez un backend distant
  # backend "s3" {
  #   bucket         = "mercatopulse-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "eu-west-1"
  #   encrypt        = true
  #   dynamodb_table = "mercatopulse-tf-lock"
  # }
}

# ══════════════════════════════════════════════════════════
# NEON POSTGRESQL — Base de données Serverless
# ══════════════════════════════════════════════════════════
provider "neon" {
  api_key = var.neon_api_key
}

resource "neon_project" "mercatopulse" {
  name      = "mercatopulse-${var.environment}"
  region_id = "aws-eu-west-1"

  branch {
    name = "main"
  }

  default_endpoint_settings {
    autoscaling_limit_min_cu = 0.25
    autoscaling_limit_max_cu = 2
    suspend_timeout_seconds  = 300
  }
}

resource "neon_database" "main" {
  project_id = neon_project.mercatopulse.id
  branch_id  = neon_project.mercatopulse.default_branch_id
  name       = "mercatopulse_${var.environment}"
  owner_name = "mercato_admin"
}

# ══════════════════════════════════════════════════════════
# UPSTASH REDIS — Cache Serverless
# ══════════════════════════════════════════════════════════
provider "upstash" {
  email   = var.upstash_email
  api_key = var.upstash_api_key
}

resource "upstash_redis_database" "cache" {
  database_name = "mercatopulse-cache-${var.environment}"
  region        = "eu-west-1"
  tls           = true
}

# ══════════════════════════════════════════════════════════
# CLOUDFLARE — DNS + WAF + CDN
# ══════════════════════════════════════════════════════════
provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

resource "cloudflare_record" "api" {
  zone_id = var.cloudflare_zone_id
  name    = "api"
  value   = var.render_app_domain
  type    = "CNAME"
  proxied = true   # Activates Cloudflare CDN + WAF
  ttl     = 1      # Auto (managed by Cloudflare when proxied)
}

resource "cloudflare_ruleset" "waf_rules" {
  zone_id = var.cloudflare_zone_id
  name    = "MercatoPULSE WAF Rules"
  kind    = "zone"
  phase   = "http_request_firewall_managed"

  rules {
    action = "managed_challenge"
    expression = "(cf.threat_score gt 30)"
    description = "Challenge high threat score IPs"
    enabled = true
  }
}

# ══════════════════════════════════════════════════════════
# OUTPUTS
# ══════════════════════════════════════════════════════════
output "neon_connection_string" {
  description = "Neon PostgreSQL connection string (sensitive)"
  value       = neon_project.mercatopulse.connection_uri
  sensitive   = true
}

output "redis_endpoint" {
  description = "Upstash Redis endpoint"
  value       = upstash_redis_database.cache.endpoint
  sensitive   = true
}
