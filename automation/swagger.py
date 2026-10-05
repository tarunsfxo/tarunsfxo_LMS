"""
automation.swagger — OpenAPI 3.0 Specification Generator
==========================================================
Auto-generates Swagger/OpenAPI docs for all automation endpoints.
Served at ``/n8n/api/docs`` via embedded Swagger UI (CDN).
"""

import json


def get_openapi_spec() -> dict:
    """Generate the OpenAPI 3.0 specification for automation endpoints."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Tarunsfxo LMS — Automation API",
            "description": "API documentation for the n8n automation integration layer.",
            "version": "1.0.0",
            "contact": {"name": "Tarunsfxo LMS"},
        },
        "servers": [{"url": "/n8n", "description": "Automation API"}],
        "tags": [
            {"name": "Webhooks", "description": "Endpoints called by n8n workflows"},
            {"name": "API", "description": "JSON API endpoints for the frontend"},
            {"name": "Health", "description": "System health monitoring"},
            {"name": "Builder", "description": "Automation Builder rule management"},
        ],
        "paths": {
            "/webhook/welcome-email": _webhook_path("Welcome Email", "Receives welcome email trigger from n8n"),
            "/webhook/course-enrolled": _webhook_path("Course Enrolled", "Receives enrollment confirmation from n8n"),
            "/webhook/certificate-ready": _webhook_path("Certificate Ready", "Receives certificate generation result"),
            "/webhook/daily-reminder": _webhook_path("Daily Reminder", "Receives daily reminder data"),
            "/webhook/weekly-report": _webhook_path("Weekly Report", "Receives weekly report data"),
            "/webhook/security-alert": _webhook_path("Security Alert", "Receives security alert from n8n"),
            "/webhook/feedback-analyzed": _webhook_path("Feedback Analyzed", "Receives sentiment analysis results"),
            "/api/workflows": {
                "get": {
                    "tags": ["API"],
                    "summary": "List all workflow configurations",
                    "security": [{"sessionAuth": []}],
                    "responses": {"200": {"description": "List of workflows"}},
                },
            },
            "/api/logs": {
                "get": {
                    "tags": ["API"],
                    "summary": "Get paginated workflow execution logs",
                    "parameters": [
                        {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                        {"name": "status", "in": "query", "schema": {"type": "string"}},
                        {"name": "workflow", "in": "query", "schema": {"type": "string"}},
                    ],
                    "security": [{"sessionAuth": []}],
                    "responses": {"200": {"description": "Paginated logs"}},
                },
            },
            "/api/stats": {
                "get": {
                    "tags": ["API"],
                    "summary": "Get automation analytics statistics",
                    "security": [{"sessionAuth": []}],
                    "responses": {"200": {"description": "Analytics data"}},
                },
            },
            "/api/health": {
                "get": {
                    "tags": ["Health"],
                    "summary": "Get system health status (cached metrics)",
                    "responses": {
                        "200": {
                            "description": "Health status",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "status": "healthy",
                                        "components": {
                                            "n8n": {"status": "up", "avg_latency_ms": 45},
                                            "redis": {"status": "up", "queue_depth": 3},
                                            "openai": {"status": "up", "avg_latency_ms": 680},
                                            "email": {"status": "up"},
                                        },
                                    }
                                }
                            },
                        }
                    },
                },
            },
            "/api/queue": {
                "get": {
                    "tags": ["API"],
                    "summary": "Get Redis queue status",
                    "security": [{"sessionAuth": []}],
                    "responses": {"200": {"description": "Queue statistics"}},
                },
            },
            "/api/builder/rules": {
                "get": {
                    "tags": ["Builder"],
                    "summary": "List all automation rules",
                    "security": [{"sessionAuth": []}],
                    "responses": {"200": {"description": "List of rules"}},
                },
                "post": {
                    "tags": ["Builder"],
                    "summary": "Create a new automation rule",
                    "security": [{"sessionAuth": []}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "trigger_event": {"type": "string"},
                                        "conditions": {"type": "array"},
                                        "actions": {"type": "array"},
                                    },
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Created rule"}},
                },
            },
        },
        "components": {
            "securitySchemes": {
                "webhookSecret": {
                    "type": "apiKey",
                    "name": "X-Webhook-Secret",
                    "in": "header",
                    "description": "Shared secret for n8n webhook authentication",
                },
                "sessionAuth": {
                    "type": "apiKey",
                    "name": "session",
                    "in": "cookie",
                    "description": "Flask session cookie (login required)",
                },
            },
        },
    }


def _webhook_path(summary: str, description: str) -> dict:
    """Generate a standard webhook endpoint path definition."""
    return {
        "post": {
            "tags": ["Webhooks"],
            "summary": summary,
            "description": description,
            "security": [{"webhookSecret": []}],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {"type": "object"},
                    }
                }
            },
            "responses": {
                "200": {"description": "Webhook processed successfully"},
                "401": {"description": "Invalid webhook secret"},
            },
        },
    }
