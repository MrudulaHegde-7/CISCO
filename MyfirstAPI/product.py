from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()
class Product(BaseModel):
    id:int
    name:str
    price:float
    quantity:int
    category:str
products=[]
@app.post("/addProduct")
def add_employees(prod:Product):
    products.append(prod)
    return {"message:successfully added"}

@app.get("/getAllProducts")
def get_employees():
    return products

@app.get("/productById/{id}")
def products_byId(id:int):
    for prod in products:
        if prod.id==id:
            return prod
    return {"message:not found"}

@app.put("/updateProduct/{id}")
def update_employee(id:int,updatedProd:Product):
    for prod in products:
        if prod.id == id:
            prod.name=updatedProd.name
            prod.price=updatedProd.price
            prod.quantity=updatedProd.quantity
            prod.category=updatedProd.category
            return prod
    return {"message:employee not found"}

@app.delete("/deleteProduct/{id}")
def del_product_byId(id:int):
    for prod in products:
        if prod.id==id:
            products.remove(prod)
            return {"message:deleted successfully"}
    return {"message:deletion failed"}

@app.get("/productsByCategory/{category}")
def findBy_category(category:str):
    result=[]
    for prod in products:
        if prod.category.lower() == category.lower():
          result.append(prod)
    return result

@app.get("/productsBelowPrice/{price}")
def get_prduct_lessThan(price:float):
    result=[]
    for prod in products:
        if prod.price<price:
            result.append(prod)
    return result

@app.get("/productCount")
def count_products():
    return {"Total products": len(products)}
