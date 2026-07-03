-- tarunsfxo LMS Database Schema (MySQL 8+))
-- This mirrors the SQLAlchemy models in models.py.
-- SQLAlchemy create_all() will generate this automatically, but this file
-- is provided for manual setup / documentation purposes.

CREATE DATABASE IF NOT EXISTS tarunsfxo_lms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tarunsfxo_lms_db;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    plan VARCHAR(20) DEFAULT 'free',
    xp INT DEFAULT 0,
    streak_count INT DEFAULT 0,
    last_active_date DATE NULL,
    avatar_seed VARCHAR(50) DEFAULT 'default',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    slug VARCHAR(50) NOT NULL UNIQUE,
    icon VARCHAR(50) DEFAULT 'code',
    color VARCHAR(20) DEFAULT '#6366f1'
) ENGINE=InnoDB;

CREATE TABLE bites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    slug VARCHAR(160) NOT NULL UNIQUE,
    summary VARCHAR(300),
    content TEXT NOT NULL,
    code_snippet TEXT,
    difficulty VARCHAR(20) DEFAULT 'beginner',
    duration_minutes INT DEFAULT 5,
    category_id INT,
    is_premium BOOLEAN DEFAULT FALSE,
    order_index INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB;

    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX ix_bites_category_id ON bites(category_id);

CREATE TABLE quiz_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bite_id INT NOT NULL,
    question VARCHAR(300) NOT NULL,
    option_a VARCHAR(200) NOT NULL,
    option_b VARCHAR(200) NOT NULL,
    option_c VARCHAR(200) NOT NULL,
    option_d VARCHAR(200) NOT NULL,
    correct_option CHAR(1) NOT NULL,
    explanation VARCHAR(300),
    FOREIGN KEY (bite_id) REFERENCES bites(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    bite_id INT NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at DATETIME NULL,
    time_spent_seconds INT DEFAULT 0,
    UNIQUE KEY uix_user_bite (user_id, bite_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (bite_id) REFERENCES bites(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE quiz_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    bite_id INT NOT NULL,
    score INT DEFAULT 0,
    total_questions INT DEFAULT 0,
    attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (bite_id) REFERENCES bites(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX ix_quiz_attempts_user_bite ON quiz_attempts(user_id, bite_id);

CREATE TABLE xp_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount INT NOT NULL,
    reason VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX ix_xp_log_user_id ON xp_log(user_id);

CREATE TABLE certificates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT,
    cert_code VARCHAR(40) NOT NULL UNIQUE,
    file_path VARCHAR(255),
    issued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    plan VARCHAR(20) NOT NULL,
    amount FLOAT NOT NULL,
    card_last4 VARCHAR(4),
    status VARCHAR(20) DEFAULT 'success',
    transaction_id VARCHAR(50) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;
