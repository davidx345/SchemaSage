"""
Express.js scaffolding generator
"""
import logging
from typing import Dict, List, Optional, Any

from models.schemas import SchemaResponse, TableInfo, ColumnInfo
from .base import APIComponent, ComponentType, APIFramework, TypeMapper, CodeTemplateEngine

logger = logging.getLogger(__name__)

class ExpressGenerator:
    """Generates Express.js scaffolding"""
    
    def __init__(self):
        self.type_mapper = TypeMapper()
        self.template_engine = CodeTemplateEngine()
    
    def generate_models(
        self, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate Mongoose/Sequelize models"""
        components = []
        
        orm_type = options.get('orm', 'mongoose') if options else 'mongoose'
        
        for table in schema.tables:
            if orm_type == 'mongoose':
                model_component = self._generate_mongoose_model(table, schema, options)
            else:
                model_component = self._generate_sequelize_model(table, schema, options)
            components.append(model_component)
        
        return components
    
    def _generate_mongoose_model(
        self, 
        table: TableInfo, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> APIComponent:
        """Generate a Mongoose model"""
        
        class_name = self.template_engine.generate_class_name(table.name)
        
        imports = [
            "const mongoose = require('mongoose');",
            "const { Schema } = mongoose;"
        ]
        
        # Generate schema fields
        fields = []
        for column in table.columns:
            mongoose_field = self._get_mongoose_field(column)
            fields.append(f"  {column.name}: {mongoose_field}")
        
        content = f'''/**
 * {class_name} Mongoose model
 */
{chr(10).join(imports)}

const {class_name.lower()}Schema = new Schema({{
{",\n".join(fields)},
  createdAt: {{
    type: Date,
    default: Date.now
  }},
  updatedAt: {{
    type: Date,
    default: Date.now
  }}
}}, {{
  timestamps: true,
  collection: '{table.name}'
}});

// Indexes
{class_name.lower()}Schema.index({{ createdAt: -1 }});

// Virtual fields
{class_name.lower()}Schema.virtual('id').get(function() {{
  return this._id.toHexString();
}});

// Instance methods
{class_name.lower()}Schema.methods.toJSON = function() {{
  const obj = this.toObject();
  obj.id = obj._id;
  delete obj._id;
  delete obj.__v;
  return obj;
}};

// Static methods
{class_name.lower()}Schema.statics.findByCustomQuery = function(query) {{
  return this.find(query);
}};

// Pre-save middleware
{class_name.lower()}Schema.pre('save', function(next) {{
  this.updatedAt = Date.now();
  next();
}});

// Pre-update middleware
{class_name.lower()}Schema.pre(['updateOne', 'findOneAndUpdate'], function() {{
  this.set({{ updatedAt: Date.now() }});
}});

const {class_name} = mongoose.model('{class_name}', {class_name.lower()}Schema);

module.exports = {class_name};
'''
        
        return APIComponent(
            name=f"{class_name}Model",
            component_type=ComponentType.MODEL,
            framework=APIFramework.EXPRESS,
            content=content,
            file_path=f"models/{table.name}.js",
            dependencies=["mongoose"],
            imports=imports,
            metadata={
                "table_name": table.name,
                "class_name": class_name,
                "orm": "mongoose"
            }
        )
    
    def _get_mongoose_field(self, column: ColumnInfo) -> str:
        """Map column type to Mongoose field"""
        
        type_map = {
            'int': 'Number',
            'bigint': 'Number',
            'varchar': 'String',
            'text': 'String',
            'boolean': 'Boolean',
            'date': 'Date',
            'datetime': 'Date',
            'time': 'String',
            'decimal': 'Number',
            'float': 'Number',
            'json': 'Schema.Types.Mixed',
            'uuid': 'String'
        }
        
        base_type = column.type.lower()
        mongoose_type = type_map.get(base_type, 'String')
        
        field_config = {"type": mongoose_type}
        
        if getattr(column, 'required', True):
            field_config["required"] = True
        
        if hasattr(column, 'unique') and column.unique:
            field_config["unique"] = True
        
        if hasattr(column, 'max_length') and column.max_length:
            field_config["maxlength"] = column.max_length
        
        if hasattr(column, 'default') and column.default is not None:
            field_config["default"] = column.default
        
        # Format as JavaScript object
        if len(field_config) == 1 and "type" in field_config:
            return mongoose_type
        else:
            config_str = ", ".join([f"{k}: {repr(v) if isinstance(v, str) else v}" for k, v in field_config.items()])
            return f"{{ {config_str} }}"
    
    def generate_controllers(
        self, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate Express controllers"""
        components = []
        
        for table in schema.tables:
            controller_component = self._generate_express_controller(table, schema, options)
            components.append(controller_component)
        
        return components
    
    def _generate_express_controller(
        self, 
        table: TableInfo, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> APIComponent:
        """Generate a single Express controller"""
        
        class_name = self.template_engine.generate_class_name(table.name)
        
        imports = [
            f"const {class_name} = require('../models/{table.name}');",
            "const { validationResult } = require('express-validator');",
            "const ApiError = require('../utils/ApiError');",
            "const catchAsync = require('../utils/catchAsync');"
        ]
        
        content = f'''/**
 * {class_name} controller
 */
{chr(10).join(imports)}

/**
 * Get all {table.name}
 */
const getAll{class_name}s = catchAsync(async (req, res) => {{
  const {{ page = 1, limit = 10, sort = '-createdAt' }} = req.query;
  
  const options = {{
    page: parseInt(page),
    limit: parseInt(limit),
    sort: sort
  }};
  
  const {table.name} = await {class_name}.find()
    .sort(options.sort)
    .limit(options.limit * 1)
    .skip((options.page - 1) * options.limit)
    .exec();
  
  const total = await {class_name}.countDocuments();
  
  res.json({{
    success: true,
    data: {table.name},
    pagination: {{
      page: options.page,
      limit: options.limit,
      total,
      pages: Math.ceil(total / options.limit)
    }}
  }});
}});

/**
 * Get {table.name} by ID
 */
const get{class_name}ById = catchAsync(async (req, res) => {{
  const {{ id }} = req.params;
  
  const {table.name.rstrip('s')} = await {class_name}.findById(id);
  
  if (!{table.name.rstrip('s')}) {{
    throw new ApiError(404, '{class_name} not found');
  }}
  
  res.json({{
    success: true,
    data: {table.name.rstrip('s')}
  }});
}});

/**
 * Create new {table.name}
 */
const create{class_name} = catchAsync(async (req, res) => {{
  const errors = validationResult(req);
  if (!errors.isEmpty()) {{
    throw new ApiError(400, 'Validation failed', errors.array());
  }}
  
  const {table.name.rstrip('s')} = new {class_name}(req.body);
  await {table.name.rstrip('s')}.save();
  
  res.status(201).json({{
    success: true,
    data: {table.name.rstrip('s')},
    message: '{class_name} created successfully'
  }});
}});

/**
 * Update {table.name}
 */
const update{class_name} = catchAsync(async (req, res) => {{
  const errors = validationResult(req);
  if (!errors.isEmpty()) {{
    throw new ApiError(400, 'Validation failed', errors.array());
  }}
  
  const {{ id }} = req.params;
  
  const {table.name.rstrip('s')} = await {class_name}.findByIdAndUpdate(
    id,
    req.body,
    {{ new: true, runValidators: true }}
  );
  
  if (!{table.name.rstrip('s')}) {{
    throw new ApiError(404, '{class_name} not found');
  }}
  
  res.json({{
    success: true,
    data: {table.name.rstrip('s')},
    message: '{class_name} updated successfully'
  }});
}});

/**
 * Delete {table.name}
 */
const delete{class_name} = catchAsync(async (req, res) => {{
  const {{ id }} = req.params;
  
  const {table.name.rstrip('s')} = await {class_name}.findByIdAndDelete(id);
  
  if (!{table.name.rstrip('s')}) {{
    throw new ApiError(404, '{class_name} not found');
  }}
  
  res.json({{
    success: true,
    message: '{class_name} deleted successfully'
  }});
}});

/**
 * Search {table.name}
 */
const search{class_name}s = catchAsync(async (req, res) => {{
  const {{ q, page = 1, limit = 10 }} = req.query;
  
  if (!q) {{
    throw new ApiError(400, 'Search query is required');
  }}
  
  const searchRegex = new RegExp(q, 'i');
  const query = {{
    $or: [
      // Add searchable fields here
      // {{ name: searchRegex }},
      // {{ description: searchRegex }}
    ]
  }};
  
  const {table.name} = await {class_name}.find(query)
    .limit(limit * 1)
    .skip((page - 1) * limit)
    .exec();
  
  const total = await {class_name}.countDocuments(query);
  
  res.json({{
    success: true,
    data: {table.name},
    pagination: {{
      page: parseInt(page),
      limit: parseInt(limit),
      total,
      pages: Math.ceil(total / limit)
    }}
  }});
}});

module.exports = {{
  getAll{class_name}s,
  get{class_name}ById,
  create{class_name},
  update{class_name},
  delete{class_name},
  search{class_name}s
}};
'''
        
        return APIComponent(
            name=f"{class_name}Controller",
            component_type=ComponentType.CONTROLLER,
            framework=APIFramework.EXPRESS,
            content=content,
            file_path=f"controllers/{table.name}Controller.js",
            dependencies=["express-validator"],
            imports=imports,
            metadata={
                "table_name": table.name,
                "class_name": class_name
            }
        )
    
    def generate_routes(
        self, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate Express routes"""
        components = []
        
        for table in schema.tables:
            route_component = self._generate_express_routes(table, schema, options)
            components.append(route_component)
        
        return components
    
    def _generate_express_routes(
        self, 
        table: TableInfo, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> APIComponent:
        """Generate routes for a single table"""
        
        class_name = self.template_engine.generate_class_name(table.name)
        route_path = self.template_engine.generate_route_path(table.name)
        
        imports = [
            "const express = require('express');",
            "const { body, param, query } = require('express-validator');",
            f"const {table.name}Controller = require('../controllers/{table.name}Controller');",
            "const auth = require('../middleware/auth');",
            "const rateLimit = require('../middleware/rateLimit');"
        ]
        
        content = f'''/**
 * {class_name} routes
 */
{chr(10).join(imports)}

const router = express.Router();

// Apply authentication to all routes
router.use(auth);

// Apply rate limiting
const {table.name}RateLimit = rateLimit({{
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
}});

router.use({table.name}RateLimit);

// Validation middleware
const validate{class_name}Creation = [
  // Add validation rules here
  // body('name').notEmpty().withMessage('Name is required'),
  // body('email').isEmail().withMessage('Valid email is required'),
];

const validate{class_name}Update = [
  // Add validation rules here
  // body('name').optional().notEmpty().withMessage('Name cannot be empty'),
];

const validateId = [
  param('id').isMongoId().withMessage('Invalid ID format')
];

const validatePagination = [
  query('page').optional().isInt({{ min: 1 }}).withMessage('Page must be a positive integer'),
  query('limit').optional().isInt({{ min: 1, max: 100 }}).withMessage('Limit must be between 1 and 100')
];

// Routes
router.get(
  '/',
  validatePagination,
  {table.name}Controller.getAll{class_name}s
);

router.get(
  '/search',
  [
    query('q').notEmpty().withMessage('Search query is required'),
    ...validatePagination
  ],
  {table.name}Controller.search{class_name}s
);

router.get(
  '/:id',
  validateId,
  {table.name}Controller.get{class_name}ById
);

router.post(
  '/',
  validate{class_name}Creation,
  {table.name}Controller.create{class_name}
);

router.put(
  '/:id',
  [
    ...validateId,
    ...validate{class_name}Update
  ],
  {table.name}Controller.update{class_name}
);

router.delete(
  '/:id',
  validateId,
  {table.name}Controller.delete{class_name}
);

module.exports = router;
'''
        
        return APIComponent(
            name=f"{class_name}Routes",
            component_type=ComponentType.ROUTE,
            framework=APIFramework.EXPRESS,
            content=content,
            file_path=f"routes/{table.name}.js",
            dependencies=["express", "express-validator"],
            imports=imports,
            metadata={
                "table_name": table.name,
                "class_name": class_name,
                "route_path": route_path
            }
        )
    
    def generate_middleware(
        self, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate Express middleware"""
        components = []
        
        # Generate common middleware
        auth_middleware = self._generate_auth_middleware()
        components.append(auth_middleware)
        
        error_middleware = self._generate_error_middleware()
        components.append(error_middleware)
        
        rate_limit_middleware = self._generate_rate_limit_middleware()
        components.append(rate_limit_middleware)
        
        return components
    
    def _generate_auth_middleware(self) -> APIComponent:
        """Generate authentication middleware"""
        
        imports = [
            "const jwt = require('jsonwebtoken');",
            "const ApiError = require('../utils/ApiError');",
            "const catchAsync = require('../utils/catchAsync');"
        ]
        
        content = f'''/**
 * Authentication middleware
 */
{chr(10).join(imports)}

const auth = catchAsync(async (req, res, next) => {{
  let token;
  
  if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {{
    token = req.headers.authorization.split(' ')[1];
  }}
  
  if (!token) {{
    throw new ApiError(401, 'Access denied. No token provided.');
  }}
  
  try {{
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  }} catch (error) {{
    throw new ApiError(401, 'Invalid token.');
  }}
}});

const authorize = (...roles) => {{
  return (req, res, next) => {{
    if (!req.user) {{
      throw new ApiError(401, 'Access denied. User not authenticated.');
    }}
    
    if (roles.length && !roles.includes(req.user.role)) {{
      throw new ApiError(403, 'Access denied. Insufficient permissions.');
    }}
    
    next();
  }};
}};

module.exports = {{ auth, authorize }};
'''
        
        return APIComponent(
            name="AuthMiddleware",
            component_type=ComponentType.MIDDLEWARE,
            framework=APIFramework.EXPRESS,
            content=content,
            file_path="middleware/auth.js",
            dependencies=["jsonwebtoken"],
            imports=imports,
            metadata={"type": "authentication"}
        )
    
    def _generate_error_middleware(self) -> APIComponent:
        """Generate error handling middleware"""
        
        imports = [
            "const ApiError = require('../utils/ApiError');"
        ]
        
        content = f'''/**
 * Error handling middleware
 */
{chr(10).join(imports)}

const errorHandler = (err, req, res, next) => {{
  let error = {{ ...err }};
  error.message = err.message;
  
  // Log error
  console.error(err);
  
  // Mongoose bad ObjectId
  if (err.name === 'CastError') {{
    const message = 'Resource not found';
    error = new ApiError(404, message);
  }}
  
  // Mongoose duplicate key
  if (err.code === 11000) {{
    const message = 'Duplicate field value entered';
    error = new ApiError(400, message);
  }}
  
  // Mongoose validation error
  if (err.name === 'ValidationError') {{
    const message = Object.values(err.errors).map(val => val.message).join(', ');
    error = new ApiError(400, message);
  }}
  
  res.status(error.statusCode || 500).json({{
    success: false,
    error: error.message || 'Server Error',
    ...(process.env.NODE_ENV === 'development' && {{ stack: err.stack }})
  }});
}};

module.exports = errorHandler;
'''
        
        return APIComponent(
            name="ErrorMiddleware",
            component_type=ComponentType.MIDDLEWARE,
            framework=APIFramework.EXPRESS,
            content=content,
            file_path="middleware/errorHandler.js",
            dependencies=[],
            imports=imports,
            metadata={"type": "error_handling"}
        )
    
    def _generate_rate_limit_middleware(self) -> APIComponent:
        """Generate rate limiting middleware"""
        
        imports = [
            "const rateLimit = require('express-rate-limit');"
        ]
        
        content = f'''/**
 * Rate limiting middleware
 */
{chr(10).join(imports)}

const createRateLimit = (options = {{}}) => {{
  const defaultOptions = {{
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // limit each IP to 100 requests per windowMs
    message: {{
      success: false,
      error: 'Too many requests from this IP, please try again later.'
    }},
    standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
    legacyHeaders: false, // Disable the `X-RateLimit-*` headers
    ...options
  }};
  
  return rateLimit(defaultOptions);
}};

// Predefined rate limiters
const authLimiter = createRateLimit({{
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // limit each IP to 5 requests per windowMs for auth routes
  message: {{
    success: false,
    error: 'Too many authentication attempts, please try again later.'
  }}
}});

const apiLimiter = createRateLimit({{
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs for API routes
}});

const strictLimiter = createRateLimit({{
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 10 // limit each IP to 10 requests per windowMs for sensitive routes
}});

module.exports = {{
  createRateLimit,
  authLimiter,
  apiLimiter,
  strictLimiter
}};
'''
        
        return APIComponent(
            name="RateLimitMiddleware",
            component_type=ComponentType.MIDDLEWARE,
            framework=APIFramework.EXPRESS,
            content=content,
            file_path="middleware/rateLimit.js",
            dependencies=["express-rate-limit"],
            imports=imports,
            metadata={"type": "rate_limiting"}
        )
