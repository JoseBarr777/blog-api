# Blog API

A Django REST Framework API for managing blog posts with markdown support, search functionality, and comprehensive documentation.

## Features

- **REST API** for blog posts with list and detail endpoints
- **Markdown support** with automatic HTML conversion and sanitization
- **Search functionality** across titles, content, and author names
- **Date filtering** for published posts
- **API documentation** with Swagger UI and ReDoc
- **Admin interface** for content management
- **CORS support** for frontend integration
- **Comprehensive test suite** included

## Tech Stack

- **Django 5.2+** - Web framework
- **Django REST Framework** - API framework
- **PostgreSQL** - Database (via psycopg2)
- **MarkdownX** - Markdown editor and processing
- **drf-spectacular** - API documentation
- **nh3** - HTML sanitization
- **django-cors-headers** - CORS support

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1/
```

### Posts
- `GET /api/v1/posts/` - List all published posts
- `GET /api/v1/posts/{slug}/` - Get specific post by slug

### Documentation
- `GET /api/docs/` - Swagger UI documentation
- `GET /api/redoc/` - ReDoc documentation
- `GET /api/schema/` - OpenAPI schema

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd blog-api
   ```

2. **Set up Python environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Configure database**
   - Set up PostgreSQL database
   - Update database settings in `blog_api/settings.py`

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser** (optional)
   ```bash
   python manage.py createsuperuser
   ```

## Usage

### Start the development server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/v1/`

### Admin interface
Access the Django admin at `http://localhost:8000/admin/` to manage posts and users.

### API Documentation
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

## API Usage Examples

### List Posts
```bash
# Get all published posts
curl "http://localhost:8000/api/v1/posts/"

# Search posts
curl "http://localhost:8000/api/v1/posts/?search=django"

# Filter by date range
curl "http://localhost:8000/api/v1/posts/?published_after=2024-01-01T00:00:00Z&published_before=2024-12-31T23:59:59Z"

# Order by creation date
curl "http://localhost:8000/api/v1/posts/?ordering=created_at"
```

### Get Post Details
```bash
curl "http://localhost:8000/api/v1/posts/my-post-slug/"
```

### Response Format

**List Response:**
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/v1/posts/?page=2",
  "previous": null,
  "results": [
    {
      "title": "My Blog Post",
      "published_at": "2024-09-14T10:00:00Z",
      "url": "http://localhost:8000/api/v1/posts/my-blog-post/"
    }
  ]
}
```

**Detail Response:**
```json
{
  "title": "My Blog Post",
  "slug": "my-blog-post",
  "body": "<p>Converted HTML from markdown</p>",
  "author": "John Doe",
  "published_at": "2024-09-14T10:00:00Z",
  "created_at": "2024-09-14T09:00:00Z",
  "updated_at": "2024-09-14T09:30:00Z"
}
```

## Testing

Run the comprehensive test suite:

```bash
# Test the API endpoints
python test_api.py

# Test with verbose output
python test_api.py --verbose

# Test only specific endpoints
python test_api.py --list-only
python test_api.py --detail-only
```

## Configuration

### Environment Variables
Set up your database and other settings in `blog_api/settings.py` or use environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `DEBUG` - Debug mode (default: True)
- `SECRET_KEY` - Django secret key

### CORS Configuration
CORS is configured in settings to allow frontend integration. Modify `CORS_ALLOWED_ORIGINS` in settings for production.

## Post Management

### Post Status
Posts have three statuses:
- `draft` - Not visible in API
- `published` - Visible in API endpoints
- `archived` - Not visible in API

### Markdown Support
- Posts support full markdown syntax
- HTML is automatically generated and sanitized
- Allowed HTML tags: `p`, `h1-h6`, `br`, `strong`, `em`, `ul`, `ol`, `li`, `a`, `blockquote`, `code`, `pre`
- Links preserve `href` and `title` attributes only

## Development

### Project Structure
- **blog_api/** - Django project settings
- **post/** - Blog post app
  - `models.py` - Post model
  - `views.py` - API views
  - `serializers.py` - DRF serializers
  - `urls.py` - URL routing
- `test_api.py` - API test suite
- `manage.py` - Django management
- `pyproject.toml` - Dependencies

### Adding New Features
1. Create migrations: `python manage.py makemigrations`
2. Apply migrations: `python manage.py migrate`
3. Update serializers and views as needed
4. Add tests to `test_api.py`

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.