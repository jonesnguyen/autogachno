# Overview

This is a full-stack web application for managing ViettelPay telecommunications services. The system provides a modern web interface for processing various telecom services including FTTH lookup, EVN electricity bill payment, mobile top-up, and TV-Internet payments. The application features a React frontend with a Node.js/Express backend, PostgreSQL database integration, and includes authentication via Replit's OAuth system.

## Recent Changes (January 10, 2025)
- **Integrated Mock API Server**: Built-in mock data endpoints replacing external Python Flask server to eliminate connectivity issues
- **Complete API Functions**: Added comprehensive API endpoints for service interaction, bulk operations, and data export
- **Enhanced Service Management**: 6 Vietnamese telecom services with sample data generation and processing simulation
- **Export Capabilities**: CSV and JSON export functionality with UTF-8 support and detailed transaction summaries

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: React 18 with TypeScript and Vite for fast development and building
- **UI Components**: Shadcn/ui component library built on Radix UI primitives for consistent, accessible interface components
- **Styling**: Tailwind CSS with CSS custom properties for theming support (light/dark modes)
- **State Management**: TanStack Query (React Query) for server state management and caching
- **Routing**: Wouter for lightweight client-side routing
- **Forms**: React Hook Form with Zod validation for type-safe form handling

## Backend Architecture
- **Runtime**: Node.js with Express.js framework using ES modules
- **Database**: PostgreSQL with Drizzle ORM for type-safe database operations
- **Authentication**: Replit's OAuth integration with session-based authentication using express-session
- **API Design**: RESTful API with structured error handling and request/response logging middleware
- **Development**: Hot module replacement in development with Vite integration

## Database Schema Design
- **User Management**: Users table for storing OAuth user information (required for Replit Auth)
- **Session Storage**: Sessions table for managing user authentication sessions
- **Service Operations**: 
  - Orders table for tracking service requests with status management
  - Service transactions table for detailed transaction records
  - System configuration table for application settings
- **Data Types**: Uses PostgreSQL enums for service types and order statuses to ensure data consistency

## Authentication & Authorization
- **OAuth Provider**: Replit's OpenID Connect implementation for secure user authentication
- **Session Management**: PostgreSQL-backed sessions with configurable TTL (1 week default)
- **Middleware**: Route-level authentication middleware that redirects unauthorized users
- **Security**: HTTP-only cookies with secure flags for production environments

## External Service Integration
- **Mock API Server**: Flask-based mock server providing sample data for testing and development
- **Service Types**: Supports six telecommunications services (FTTH lookup, EVN billing, mobile top-up, etc.)
- **Data Fetching**: Client-side API calls to mock services with error handling and loading states

## Development Workflow
- **Build System**: Vite for frontend bundling with esbuild for server-side bundling
- **Database Migrations**: Drizzle Kit for schema migrations with push-based deployment
- **Development Server**: Concurrent frontend/backend development with HMR support
- **Environment Configuration**: Environment variables for database connection and authentication settings

# External Dependencies

## Database & ORM
- **PostgreSQL**: Primary database via Neon Database serverless platform
- **Drizzle ORM**: Type-safe database operations with automatic TypeScript inference
- **Connection Pooling**: @neondatabase/serverless for optimized database connections

## Authentication Services
- **Replit OAuth**: OpenID Connect integration for user authentication
- **Session Storage**: connect-pg-simple for PostgreSQL-backed session management

## UI & Styling Framework
- **Radix UI**: Accessible, unstyled component primitives
- **Tailwind CSS**: Utility-first CSS framework with custom design system
- **Shadcn/ui**: Pre-built component library with consistent design patterns

## Development Tools
- **Vite**: Frontend build tool with HMR and TypeScript support
- **React Query**: Server state management with caching and synchronization
- **Zod**: Runtime type validation for API responses and form data

## Mock Services
- **Flask API**: Python-based mock server for service data simulation
- **CORS Support**: Cross-origin resource sharing for development integration