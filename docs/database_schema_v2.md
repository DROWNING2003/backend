# 数据库结构设计文档 v2.0

## 概述

本文档描述了GitHub仓库学习平台的精简数据库结构设计，包括所有表的定义、字段说明、索引和关系。

## 数据库配置

- **数据库类型**: MySQL 8.0+
- **字符集**: utf8mb4
- **排序规则**: utf8mb4_unicode_ci
- **时区**: UTC
- **设计原则**: 精简高效、灵活扩展、易于维护

## 重构说明

### v2.0 重构内容
- **删除废弃表**: levels, tutorial_templates, user_chapter_progress, chapters
- **精简表结构**: 减少冗余字段，使用JSON字段提高灵活性
- **优化关系**: 简化表间关系，提高查询性能
- **统一设计**: 标准化字段命名和数据类型

### 核心表概览
- **任务进度管理**: `user_progress`, `tutorials`, `user_achievements`
- **课程管理**: `courses`
- **仓库管理**: `repositories`, `repository_files`
- **任务管理**: `crawl_tasks`
- **缓存管理**: `llm_cache`

---

## 1. 用户进度表 (user_progress)

**用途**: 存储用户学习进度信息，支持灵活的章节进度管理

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键ID |
| user_id | VARCHAR(255) | NOT NULL, INDEX | 用户ID |
| tutorial_id | INT | NOT NULL | 教程ID |
| status | VARCHAR(50) | DEFAULT 'not_started' | 状态: not_started, in_progress, completed, paused |
| progress_percentage | FLOAT | DEFAULT 0.0 | 完成百分比 (0-100) |
| current_step | VARCHAR(255) | NULL | 当前学习步骤/章节 |
| total_time_spent | INT | DEFAULT 0 | 总学习时间(分钟) |
| score | FLOAT | DEFAULT 0.0 | 总分数 |
| extra_data | JSON | NULL | 扩展数据：章节进度、成就等 |
| started_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 开始时间 |
| last_accessed_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 最后访问时间 |
| completed_at | DATETIME | NULL | 完成时间 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX idx_user_tutorial (user_id, tutorial_id)
- INDEX idx_status (status)
- INDEX idx_updated_at (updated_at)

**extra_data JSON结构示例**:
```json
{
  "chapters": {
    "1": {
      "status": "completed",
      "score": 90.0,
      "time_spent": 45,
      "attempts": 1,
      "completed_at": "2025-01-01T11:00:00Z"
    },
    "2": {
      "status": "in_progress",
      "score": 80.0,
      "time_spent": 30,
      "attempts": 1
    }
  },
  "achievements": ["first_chapter_completed"],
  "notes": "学习进展顺利"
}
```

---

## 2. 教程表 (tutorials)

**用途**: 存储教程基本信息和章节结构

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键ID |
| title | VARCHAR(255) | NOT NULL | 教程标题 |
| description | TEXT | NULL | 教程描述 |
| difficulty | VARCHAR(50) | DEFAULT 'beginner' | 难度: beginner, intermediate, advanced |
| estimated_time | INT | DEFAULT 0 | 预估学习时间(分钟) |
| is_active | BOOLEAN | DEFAULT TRUE | 是否激活 |
| extra_data | JSON | NULL | 扩展数据：章节信息、统计数据等 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX idx_difficulty (difficulty)
- INDEX idx_is_active (is_active)

**extra_data JSON结构示例**:
```json
{
  "tags": ["python", "programming", "beginner"],
  "chapters": [
    {
      "id": 1,
      "title": "Python环境搭建",
      "description": "学习如何安装和配置Python开发环境",
      "estimated_time": 30,
      "order_index": 1
    },
    {
      "id": 2,
      "title": "基础语法",
      "description": "掌握Python的基本语法和数据类型",
      "estimated_time": 45,
      "order_index": 2
    }
  ],
  "statistics": {
    "total_enrollments": 150,
    "average_rating": 4.5,
    "completion_rate": 0.78
  }
}
```

---

## 3. 用户成就表 (user_achievements)

**用途**: 存储用户获得的成就和奖励

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键ID |
| user_id | VARCHAR(255) | NOT NULL, INDEX | 用户ID |
| achievement_type | VARCHAR(100) | NOT NULL | 成就类型 |
| achievement_name | VARCHAR(255) | NOT NULL | 成就名称 |
| points | INT | DEFAULT 0 | 获得积分 |
| related_id | INT | NULL | 关联ID（教程/章节等） |
| extra_data | JSON | NULL | 扩展数据：描述、图标等 |
| earned_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 获得时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX idx_user_id (user_id)
- INDEX idx_achievement_type (achievement_type)
- INDEX idx_earned_at (earned_at)

---

## 4. 课程表 (courses)

**用途**: 存储课程信息（精简版，移除level_id依赖）

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键ID |
| title | VARCHAR(255) | NOT NULL | 课程标题 |
| description | TEXT | NULL | 课程描述 |
| github_url | VARCHAR(500) | NULL | GitHub仓库URL |
| difficulty | INT | DEFAULT 1 | 课程难度(1-10) |
| estimated_time | INT | NULL | 预估学习时间(分钟) |
| is_published | BOOLEAN | DEFAULT FALSE | 是否发布 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX idx_difficulty (difficulty)
- INDEX idx_is_published (is_published)
- INDEX idx_title (title)

---

## 5. 仓库表 (repositories)

**用途**: 存储GitHub仓库信息

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键ID |
| name | VARCHAR(255) | NOT NULL | 仓库名称 |
| full_name | VARCHAR(255) | NOT NULL, UNIQUE | 完整仓库名 |
| description | TEXT | NULL | 仓库描述 |
| url | VARCHAR(500) | NOT NULL | 仓库URL |
| clone_url | VARCHAR(500) | NULL | 克隆URL |
| default_branch | VARCHAR(100) | DEFAULT 'main' | 默认分支 |
| language | VARCHAR(50) | NULL | 主要编程语言 |
| stars_count | INT | DEFAULT 0 | 星标数 |
| forks_count | INT | DEFAULT 0 | 分叉数 |
| is_private | BOOLEAN | DEFAULT FALSE | 是否私有 |
| status | VARCHAR(50) | DEFAULT 'pending' | 状态: pending, crawling, completed, failed |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- UNIQUE KEY uk_full_name (full_name)
- INDEX idx_language (language)
- INDEX idx_status (status)

---

## 6. 仓库文件表 (repository_files)

**用途**: 存储仓库文件内容和元数据

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键ID |
| repository_id | INT | NOT NULL, FOREIGN KEY | 仓库ID |
| file_path | VARCHAR(1000) | NOT NULL | 文件路径 |
| file_name | VARCHAR(255) | NOT NULL | 文件名 |
| file_type | VARCHAR(50) | NULL | 文件类型 |
| file_size | BIGINT | DEFAULT 0 | 文件大小(字节) |
| content | LONGTEXT | NULL | 文件内容 |
| content_hash | VARCHAR(64) | NULL | 内容哈希值 |
| language | VARCHAR(50) | NULL | 编程语言 |
| is_binary | BOOLEAN | DEFAULT FALSE | 是否二进制文件 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- FOREIGN KEY fk_repository (repository_id) REFERENCES repositories(id)
- INDEX idx_file_path (repository_id, file_path)
- INDEX idx_file_type (file_type)
- INDEX idx_language (language)
- INDEX idx_content_hash (content_hash)

---

## 7. 爬取任务表 (crawl_tasks)

**用途**: 管理仓库爬取任务

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键ID |
| repository_id | INT | NOT NULL, FOREIGN KEY | 仓库ID |
| task_type | VARCHAR(50) | NOT NULL | 任务类型 |
| status | VARCHAR(50) | DEFAULT 'pending' | 状态: pending, running, completed, failed |
| progress | FLOAT | DEFAULT 0.0 | 进度百分比 |
| result | JSON | NULL | 任务结果 |
| error_message | TEXT | NULL | 错误信息 |
| started_at | DATETIME | NULL | 开始时间 |
| completed_at | DATETIME | NULL | 完成时间 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- FOREIGN KEY fk_repository_task (repository_id) REFERENCES repositories(id)
- INDEX idx_status (status)
- INDEX idx_task_type (task_type)

---

## 8. LLM缓存表 (llm_cache)

**用途**: 缓存LLM API调用结果

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 主键ID |
| cache_key | VARCHAR(255) | NOT NULL, UNIQUE | 缓存键 |
| prompt | TEXT | NOT NULL | 提示词 |
| response | TEXT | NOT NULL | 响应内容 |
| model | VARCHAR(100) | NOT NULL | 使用的模型 |
| tokens_used | INT | DEFAULT 0 | 使用的token数 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| expires_at | DATETIME | NULL | 过期时间 |

**索引**:
- PRIMARY KEY (id)
- UNIQUE KEY uk_cache_key (cache_key)
- INDEX idx_model (model)
- INDEX idx_expires_at (expires_at)

---

## 数据关系图

```
user_progress ──┐
                ├── tutorials
user_achievements ──┘

courses (独立表)

repositories ──── repository_files
    │
    └── crawl_tasks

llm_cache (独立表)
```

---

## 性能优化建议

### 1. 索引优化
- 为常用查询字段创建复合索引
- 定期分析慢查询并优化索引

### 2. JSON字段优化
- 使用MySQL 8.0的JSON函数进行查询
- 为JSON字段中的常用路径创建虚拟列索引

### 3. 分区策略
- 对大表按时间分区（如按月分区）
- 考虑对user_progress表按user_id哈希分区

### 4. 缓存策略
- 使用Redis缓存热点数据
- 实现查询结果缓存机制

---

## 迁移说明

### 从v1.0迁移到v2.0
1. 备份现有数据
2. 删除废弃表：levels, tutorial_templates, user_chapter_progress, chapters
3. 创建新表结构
4. 数据迁移：将章节进度合并到user_progress.extra_data中
5. 更新应用代码以适配新结构

### 迁移脚本
参考 `migrate_database_v2.py` 和 `simple_migrate_v2.py`
