CREATE DATABASE IF NOT EXISTS hayyo_kb
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE hayyo_kb;

CREATE TABLE IF NOT EXISTS qa_rounds (
  round_id VARCHAR(64) NOT NULL PRIMARY KEY,
  conv_id VARCHAR(64) NOT NULL,
  created_at DATETIME(3) NOT NULL,
  updated_at DATETIME(3) NOT NULL,
  original_query TEXT,
  rewrite_query TEXT,
  same_topic TINYINT NULL,
  named_feature_ids JSON NULL,
  lanes JSON NULL,
  c_gen JSON NULL,
  answer MEDIUMTEXT,
  status VARCHAR(32) NOT NULL,
  models JSON NULL,
  user_id VARCHAR(64) NULL,
  owner_id VARCHAR(64) NULL,
  tenant_id VARCHAR(64) NULL,
  role VARCHAR(64) NULL,
  feedback VARCHAR(16) NULL,
  feedback_at DATETIME(3) NULL,
  INDEX idx_qa_rounds_created (created_at),
  INDEX idx_qa_rounds_status (status),
  INDEX idx_qa_rounds_conv (conv_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_roles (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  name VARCHAR(64) NOT NULL,
  is_super TINYINT NOT NULL DEFAULT 0,
  is_preset TINYINT NOT NULL DEFAULT 0,
  created_at DATETIME(3) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_role_permissions (
  role_id VARCHAR(64) NOT NULL,
  perm_code VARCHAR(64) NOT NULL,
  PRIMARY KEY (role_id, perm_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_accounts (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  username VARCHAR(64) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role_id VARCHAR(64) NOT NULL,
  enabled TINYINT NOT NULL DEFAULT 1,
  tenant_id VARCHAR(64) NULL,
  created_at DATETIME(3) NOT NULL,
  updated_at DATETIME(3) NOT NULL,
  UNIQUE KEY uk_kb_accounts_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_sessions (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  account_id VARCHAR(64) NOT NULL,
  created_at DATETIME(3) NOT NULL,
  expires_at DATETIME(3) NOT NULL,
  revoked_at DATETIME(3) NULL,
  INDEX idx_kb_sessions_account (account_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_login_locks (
  username VARCHAR(64) NOT NULL PRIMARY KEY,
  fail_count INT NOT NULL DEFAULT 0,
  locked_until DATETIME(3) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_audit_logs (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  actor_id VARCHAR(64) NULL,
  actor_username VARCHAR(64) NULL,
  action VARCHAR(64) NOT NULL,
  object VARCHAR(255) NULL,
  ip VARCHAR(64) NULL,
  created_at DATETIME(3) NOT NULL,
  detail JSON NULL,
  INDEX idx_kb_audit_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS kb_conversations (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  account_id VARCHAR(64) NOT NULL,
  title VARCHAR(255) NOT NULL,
  title_locked TINYINT NOT NULL DEFAULT 0,
  payload MEDIUMTEXT NULL,
  created_at DATETIME(3) NOT NULL,
  updated_at DATETIME(3) NOT NULL,
  INDEX idx_kb_convs_account (account_id, updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
