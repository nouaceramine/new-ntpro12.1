"""
Products Routes - Extracted from server.py
Full CRUD, pagination, quick search, barcode/SKU generation
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid


def create_products_routes(db, get_current_user, get_tenant_admin, require_tenant):
    from utils.permissions import create_permission_checker
    require_permission = create_permission_checker(db, get_current_user)
    router = APIRouter(prefix="/products", tags=["products"])

    # ── Inline Models ──
    class PaginatedProductsResponse(BaseModel):
        items: list
        total: int
        page: int
        page_size: int
        total_pages: int

    class QuickSearchProduct(BaseModel):
        id: str
        name_ar: str
        name_en: str
        barcode: Optional[str] = None
        article_code: Optional[str] = None
        retail_price: float = 0
        wholesale_price: float = 0
        quantity: int = 0
        min_quantity: int = 0
        family_id: Optional[str] = None
        family_name: Optional[str] = None
        image_url: Optional[str] = None

    class QuickSearchResponse(BaseModel):
        results: List[QuickSearchProduct]
        total: int
        families: Optional[List[dict]] = None

    # ── Create Product ──
    @router.post("", status_code=201)
    async def create_product(product: dict, admin: dict = Depends(require_permission("products.create"))):
        from models.schemas import ProductCreate, ProductResponse
        p = ProductCreate(**product)
        product_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        existing = await db.products.find_one({
            "$or": [{"name_en": p.name_en}, {"name_ar": p.name_ar}]
        })
        if existing:
            raise HTTPException(status_code=409, detail=f"منتج بنفس الاسم موجود مسبقاً: {existing.get('name_ar') or existing.get('name_en')}")

        family_name = ""
        if p.family_id:
            family = await db.product_families.find_one({"id": p.family_id}, {"_id": 0, "name_ar": 1})
            if family:
                family_name = family["name_ar"]

        product_doc = {
            "id": product_id,
            "name_en": p.name_en, "name_ar": p.name_ar,
            "description_en": p.description_en or "",
            "description_ar": p.description_ar or "",
            "purchase_price": p.purchase_price,
            "wholesale_price": p.wholesale_price,
            "retail_price": p.retail_price,
            "super_wholesale_price": p.super_wholesale_price,
            "quantity": p.quantity,
            "image_url": p.image_url or "",
            "compatible_models": p.compatible_models,
            "low_stock_threshold": p.low_stock_threshold,
            "barcode": p.barcode or "",
            "article_code": p.article_code or "",
            "family_id": p.family_id or "",
            "family_name": family_name,
            "use_average_price": p.use_average_price or False,
            "created_at": now, "updated_at": now
        }
        await db.products.insert_one(product_doc)
        product_doc.pop("_id", None)
        return product_doc

    # ── Get Products ──
    @router.get("")
    async def get_products(search: Optional[str] = None, model: Optional[str] = None, barcode: Optional[str] = None, family_id: Optional[str] = None, user: dict = Depends(require_permission("products.view"))):
        query = {}
        if barcode:
            query["barcode"] = barcode
        elif search:
            query["$or"] = [
                {"name_en": {"$regex": search, "$options": "i"}},
                {"name_ar": {"$regex": search, "$options": "i"}},
                {"description_en": {"$regex": search, "$options": "i"}},
                {"description_ar": {"$regex": search, "$options": "i"}},
                {"compatible_models": {"$regex": search, "$options": "i"}},
                {"barcode": {"$regex": search, "$options": "i"}},
                {"article_code": {"$regex": search, "$options": "i"}}
            ]
        if model:
            if "$or" in query:
                query = {"$and": [{"$or": query["$or"]}, {"compatible_models": {"$regex": model, "$options": "i"}}]}
            else:
                query["compatible_models"] = {"$regex": model, "$options": "i"}
        if family_id:
            if "$and" in query:
                query["$and"].append({"family_id": family_id})
            elif "$or" in query:
                query = {"$and": [{"$or": query["$or"]}, {"family_id": family_id}]}
            else:
                query["family_id"] = family_id

        products = await db.products.find(query, {"_id": 0}).to_list(1000)

        family_ids = list(set(p.get("family_id") for p in products if p.get("family_id") and not p.get("family_name")))
        families_map = {}
        if family_ids:
            families = await db.product_families.find({"id": {"$in": family_ids}}, {"_id": 0, "id": 1, "name_ar": 1}).to_list(len(family_ids))
            families_map = {f["id"]: f.get("name_ar", "") for f in families}

        product_ids = [p["id"] for p in products if not p.get("last_purchase_date")]
        last_purchases_map = {}
        if product_ids:
            pipeline = [
                {"$match": {"items.product_id": {"$in": product_ids}}},
                {"$sort": {"created_at": -1}},
                {"$unwind": "$items"},
                {"$match": {"items.product_id": {"$in": product_ids}}},
                {"$group": {"_id": "$items.product_id", "last_date": {"$first": "$created_at"}}}
            ]
            last_purchases = await db.purchases.aggregate(pipeline).to_list(len(product_ids))
            last_purchases_map = {lp["_id"]: lp["last_date"] for lp in last_purchases}

        for product in products:
            if product.get("family_id") and not product.get("family_name"):
                product["family_name"] = families_map.get(product["family_id"], "")
            elif not product.get("family_name"):
                product["family_name"] = ""
            if not product.get("article_code"):
                product["article_code"] = ""
            if not product.get("last_purchase_date") and product["id"] in last_purchases_map:
                product["last_purchase_date"] = last_purchases_map[product["id"]]
        return products

    # ── Paginated Products ──
    @router.get("/paginated")
    async def get_products_paginated(
        search: Optional[str] = None, model: Optional[str] = None,
        barcode: Optional[str] = None, family_id: Optional[str] = None,
        page: int = 1, page_size: int = 20,
        user: dict = Depends(require_tenant)
    ):
        query = {}
        if barcode:
            query["barcode"] = barcode
        elif search:
            query["$or"] = [
                {"name_en": {"$regex": search, "$options": "i"}},
                {"name_ar": {"$regex": search, "$options": "i"}},
                {"description_en": {"$regex": search, "$options": "i"}},
                {"description_ar": {"$regex": search, "$options": "i"}},
                {"compatible_models": {"$regex": search, "$options": "i"}},
                {"barcode": {"$regex": search, "$options": "i"}},
                {"article_code": {"$regex": search, "$options": "i"}}
            ]
        if model:
            if "$or" in query:
                query = {"$and": [{"$or": query["$or"]}, {"compatible_models": {"$regex": model, "$options": "i"}}]}
            else:
                query["compatible_models"] = {"$regex": model, "$options": "i"}
        if family_id:
            if "$and" in query:
                query["$and"].append({"family_id": family_id})
            elif "$or" in query:
                query = {"$and": [{"$or": query["$or"]}, {"family_id": family_id}]}
            else:
                query["family_id"] = family_id

        total = await db.products.count_documents(query)
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        skip = (page - 1) * page_size
        products = await db.products.find(query, {"_id": 0}).skip(skip).limit(page_size).to_list(page_size)

        for product in products:
            if product.get("family_id") and not product.get("family_name"):
                family = await db.product_families.find_one({"id": product["family_id"]}, {"_id": 0, "name_ar": 1})
                product["family_name"] = family["name_ar"] if family else ""
            elif not product.get("family_name"):
                product["family_name"] = ""
            if not product.get("article_code"):
                product["article_code"] = ""

        return {"items": products, "total": total, "page": page, "page_size": page_size, "total_pages": total_pages}

    # ── Quick Search ──
    @router.get("/quick-search")
    async def quick_search_products(
        q: str = "", limit: int = 15, family_id: Optional[str] = None,
        stock_filter: Optional[str] = None, min_price: Optional[float] = None,
        max_price: Optional[float] = None, include_families: bool = False,
        user: dict = Depends(require_tenant)
    ):
        conditions = []
        if q and len(q) >= 1:
            conditions.append({
                "$or": [
                    {"barcode": q},
                    {"article_code": {"$regex": f"^{q}", "$options": "i"}},
                    {"name_ar": {"$regex": q, "$options": "i"}},
                    {"name_en": {"$regex": q, "$options": "i"}},
                    {"barcode": {"$regex": q, "$options": "i"}},
                ]
            })
        if family_id:
            conditions.append({"family_id": family_id})
        if stock_filter == "out":
            conditions.append({"quantity": {"$lte": 0}})
        elif stock_filter == "low":
            conditions.append({"$expr": {"$lte": ["$quantity", "$min_quantity"]}})
        elif stock_filter == "available":
            conditions.append({"quantity": {"$gt": 0}})
        if min_price is not None:
            conditions.append({"retail_price": {"$gte": min_price}})
        if max_price is not None:
            conditions.append({"retail_price": {"$lte": max_price}})

        search_query = {"$and": conditions} if conditions else {}
        projection = {
            "_id": 0, "id": 1, "name_ar": 1, "name_en": 1, "barcode": 1,
            "article_code": 1, "retail_price": 1, "wholesale_price": 1,
            "quantity": 1, "min_quantity": 1, "family_id": 1, "image_url": 1
        }

        total = await db.products.count_documents(search_query)
        products = await db.products.find(search_query, projection).limit(limit).to_list(limit)

        for product in products:
            if product.get("family_id"):
                family = await db.product_families.find_one({"id": product["family_id"]}, {"_id": 0, "name_ar": 1})
                product["family_name"] = family.get("name_ar", "") if family else ""
            else:
                product["family_name"] = ""
            if "min_quantity" not in product:
                product["min_quantity"] = 0

        def sort_key(p):
            if q and p.get("barcode") == q:
                return 0
            if q and p.get("article_code", "").lower().startswith(q.lower()):
                return 1
            return 2

        if q:
            products.sort(key=sort_key)

        families_list = None
        if include_families:
            families_list = await db.product_families.find({}, {"_id": 0, "id": 1, "name_ar": 1, "name_en": 1}).to_list(100)

        return {"results": products, "total": total, "families": families_list}

    # ── Generate Barcode ──
    @router.get("/generate-barcode")
    async def generate_barcode(article_code: Optional[str] = None):
        import random
        if article_code:
            try:
                num = article_code.replace("AR", "").lstrip("0") or "1"
                num = int(num)
            except (ValueError, AttributeError):
                num = random.randint(1, 99999)
            prefix = "213"
            company = "0001"
            product_num = str(num).zfill(5)
            code = prefix + company + product_num
            odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
            even_sum = sum(int(code[i]) for i in range(1, 12, 2))
            check_digit = (10 - ((odd_sum + even_sum * 3) % 10)) % 10
            return {"barcode": code + str(check_digit)}

        while True:
            import random
            prefix = "213"
            company = "0001"
            product_num = str(random.randint(10000, 99999))
            code = prefix + company + product_num
            odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
            even_sum = sum(int(code[i]) for i in range(1, 12, 2))
            check_digit = (10 - ((odd_sum + even_sum * 3) % 10)) % 10
            barcode = code + str(check_digit)
            existing = await db.products.find_one({"barcode": barcode})
            if not existing:
                return {"barcode": barcode}

    # ── Generate SKU ──
    @router.get("/generate-sku")
    async def generate_sku(family_id: Optional[str] = None):
        prefix = "SG"
        if family_id:
            family = await db.product_families.find_one({"id": family_id}, {"_id": 0, "name_en": 1})
            if family:
                prefix = family["name_en"][:2].upper()
        count = await db.products.count_documents({})
        return {"sku": f"{prefix}-{str(count + 1).zfill(5)}"}

    # ── Generate Article Code ──
    @router.get("/generate-article-code")
    async def generate_article_code():
        pipeline = [
            {"$match": {"article_code": {"$regex": "^AR\\d{4}$"}}},
            {"$project": {"num": {"$toInt": {"$substr": ["$article_code", 2, 4]}}}},
            {"$sort": {"num": -1}},
            {"$limit": 1}
        ]
        result = await db.products.aggregate(pipeline).to_list(1)
        next_num = result[0]["num"] + 1 if result else 1
        return {"article_code": f"AR{str(next_num).zfill(4)}"}

    # ── Low Stock Alert ──
    @router.get("/alerts/low-stock")
    async def get_low_stock_products(admin: dict = Depends(require_permission("products.view"))):
        pipeline = [
            {"$match": {"$expr": {"$lt": ["$quantity", {"$ifNull": ["$low_stock_threshold", 10]}]}}},
            {"$project": {"_id": 0}}
        ]
        return await db.products.aggregate(pipeline).to_list(1000)

    # ── Get Single Product ──
    @router.get("/{product_id}")
    async def get_product(product_id: str, user: dict = Depends(require_permission("products.view"))):
        product = await db.products.find_one({"id": product_id}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail="المنتج غير موجود")
        if not product.get("family_name"):
            product["family_name"] = ""
        if not product.get("article_code"):
            product["article_code"] = ""
        return product

    # ── Update Product ──
    @router.put("/{product_id}")
    async def update_product(product_id: str, updates: dict, admin: dict = Depends(require_permission("products.edit"))):
        product = await db.products.find_one({"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="المنتج غير موجود")

        update_data = {k: v for k, v in updates.items() if v is not None and k not in ["id"]}
        if "family_id" in update_data and update_data["family_id"]:
            family = await db.product_families.find_one({"id": update_data["family_id"]}, {"_id": 0, "name_ar": 1})
            update_data["family_name"] = family["name_ar"] if family else ""

        old_price = product.get("retail_price", 0)
        new_price = update_data.get("retail_price", old_price)
        if new_price != old_price:
            await db.price_history.insert_one({
                "id": str(uuid.uuid4()),
                "product_id": product_id,
                "old_price": old_price,
                "new_price": new_price,
                "changed_by": admin.get("name", admin.get("email", "")),
                "created_at": datetime.now(timezone.utc).isoformat()
            })

        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.products.update_one({"id": product_id}, {"$set": update_data})
        updated = await db.products.find_one({"id": product_id}, {"_id": 0})
        return updated

    # ── Delete Product ──
    @router.delete("/{product_id}")
    async def delete_product(product_id: str, admin: dict = Depends(require_permission("products.delete"))):
        result = await db.products.delete_one({"id": product_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="المنتج غير موجود")
        return {"message": "تم حذف المنتج بنجاح"}

    return router
