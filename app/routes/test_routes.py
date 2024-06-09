from flask import current_app as app, render_template, request, redirect, url_for, jsonify
from ..models.test_model import TestModel, TestData
from ..db import get_db

@app.route('/')
def index():
    db = next(get_db())
    tests = db.query(TestModel).all()
    return jsonify([{"id": test.id, "uid": test.uid, "name": test.name} for test in tests])

@app.route('/add_test', methods=['POST'])
def add_test():
    db = next(get_db())
    test_data = TestData(**request.json)
    new_test = TestModel(uid=test_data.uid, name=test_data.name)
    db.add(new_test)
    db.commit()
    return jsonify({"message": "Test added successfully"}), 201
