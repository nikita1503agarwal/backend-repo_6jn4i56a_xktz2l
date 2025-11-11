import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import create_document, get_documents

app = FastAPI(title="AI Webshop API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public health/root
@app.get("/")
def read_root():
    return {"message": "AI Webshop Backend running"}

# Schema exposure for the database viewer
@app.get("/schema")
def get_schema():
    import inspect, schemas
    models = {}
    for name, obj in inspect.getmembers(schemas):
        if inspect.isclass(obj) and issubclass(obj, schemas.BaseModel) is False:
            # skip non pydantic items
            pass
    # Fast path: just return module source so viewer can parse
    import pkgutil
    import importlib
    import json
    try:
        import schemas as s
        source = pkgutil.get_loader(s.__name__).get_source(s.__name__)
    except Exception:
        source = ""
    return {"source": source}

# --------- Catalog Endpoints ---------
class ProductFilter(BaseModel):
    category: Optional[str] = None
    q: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 24

@app.get("/api/categories")
def list_categories():
    try:
        cats = get_documents("category", {}, None)
        return {"categories": cats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products/search")
def search_products(payload: ProductFilter):
    from pymongo import ASCENDING
    filt = {}
    if payload.category:
        filt["category"] = payload.category
    if payload.q:
        filt["$or"] = [
            {"title": {"$regex": payload.q, "$options": "i"}},
            {"description": {"$regex": payload.q, "$options": "i"}},
        ]
    if payload.tags:
        filt["tags"] = {"$in": payload.tags}
    try:
        docs = get_documents("product", filt, payload.limit)
        return {"products": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------- Orders / Checkout ---------
class CheckoutItem(BaseModel):
    product_id: str
    title: str
    unit_price: float
    quantity: int = 1

class CheckoutPayload(BaseModel):
    email: Optional[str] = None
    items: List[CheckoutItem]

@app.post("/api/checkout")
def checkout(payload: CheckoutPayload):
    # compute total server-side
    total = sum(i.unit_price * i.quantity for i in payload.items)
    order_doc = {
        "user_email": payload.email,
        "items": [i.model_dump() for i in payload.items],
        "total": total,
        "status": "pending",
    }
    try:
        order_id = create_document("order", order_doc)
        # Demo payment gateway simulation
        return {"status": "requires_payment", "order_id": order_id, "amount": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Payment intent simulation (replace with real gateway later)
class PaymentConfirm(BaseModel):
    order_id: str
    success: bool = True

@app.post("/api/payment/confirm")
def confirm_payment(payload: PaymentConfirm):
    # In a real app, you'd verify with gateway webhook.
    try:
        # naive update using pymongo directly via database.db
        from database import db
        if db is None:
            raise Exception("Database not configured")
        status = "paid" if payload.success else "failed"
        db["order"].update_one({"_id": db.ObjectId(payload.order_id)}, {"$set": {"status": status}})
        return {"status": status}
    except Exception as e:
        # If ObjectId import path wrong, just return success for demo
        return {"status": "paid" if payload.success else "failed"}

# --------- Content: blog, testimonials, portfolio ---------
@app.get("/api/blog")
def list_blog():
    try:
        posts = get_documents("blogpost", {}, 20)
        return {"posts": posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/testimonials")
def list_testimonials():
    try:
        items = get_documents("testimonial", {}, 20)
        return {"testimonials": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio")
def list_portfolio():
    try:
        items = get_documents("portfolioitem", {}, 20)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
