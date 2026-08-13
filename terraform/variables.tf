variable "environment" {
  description = "Deployment environment (staging | production)"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be 'staging' or 'production'."
  }
}

variable "neon_api_key" {
  description = "Neon.tech API key for PostgreSQL provisioning"
  type        = string
  sensitive   = true
}

variable "upstash_email" {
  description = "Upstash account email for Redis provisioning"
  type        = string
  sensitive   = true
}

variable "upstash_api_key" {
  description = "Upstash API key for Redis provisioning"
  type        = string
  sensitive   = true
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token with DNS + WAF permissions"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID for the domain"
  type        = string
}

variable "render_app_domain" {
  description = "Render app domain (e.g. mercatopulse-api.onrender.com)"
  type        = string
  default     = "mercatopulse-api.onrender.com"
}
