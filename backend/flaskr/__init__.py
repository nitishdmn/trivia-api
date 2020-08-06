import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import sys
from models import db, setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    
    
    CORS()
    cors = CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    
    @app.after_request
    def after_request(response):
        """
        Adds response headers after request

        Args:
            response: The response object to add headers to

        Returns:
            response: The response object that the headers were added to
        """
        response.headers.add('Access-Control-Allow-Origin', '*')

        response.headers.add('Access-Control-Allow-Headers', 
                              'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods',  
                              'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    # performign pagination on questions list
    def paginate_questions(request, selection):
        """Retrieve questions for the current page only

        Args:
            questions: A list of Question objects
            page: An int representing the page number to retrieve questions for

        Returns:
            A list of dicts representing questions for the given page
        """
        
        page = request.args.get('page', 1, type=int)
        start =  (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        questions = [question.format() for question in selection]
        current_questions = questions[start:end]

        return current_questions

    #return the categories
    @app.route('/categories')
    def get_categories():
      categories = Category.query.all()
      categories_formatted = {category.id:category.type for category in categories}
      return categories_formatted

    @app.route('/api/categories', methods=['GET', 'POST'])
    
    def handle_categories():
        try:
            if request.method == 'GET':
                try:
                    selection = Category.query.order_by('id').all()
                    result = [item.format for item in selection]
                    if not result:
                        abort(400)
                    return jsonify({
                        'success': True,
                        'categories': result,
                        'total_categories': len(Category.query.all())
                    })
                except():
                    abort(500)

            if request.method == 'POST':
                error = False

                data = request.get_json()

                new_category = Category(
                    type=data.get('type', None),
                )

                if not new_category.type:
                    abort(400)

                # check if existed
                duplicate_category = Category.query.filter(Category.type == new_category.type).all()

                if bool(duplicate_category):
                    abort(409)

                try:
                    db.session.add(new_category)
                    db.session.commit()
                except():
                    error = True
                    print(sys.exc_info())
                    abort(400)

                selection = Category.query.order_by('id').all()
                result = [item.format for item in selection]

                return jsonify({
                    'success': True,
                    'created': new_category.id,
                    'category created': new_category.type,
                    'categories': result,
                    'total_categories': len(Category.query.all())
                }), 201

        except():
            abort(500)

    
    
    @app.route('/questions',  methods=['GET'])
       
    def get_questions_by_id():
        """Route handler for endpoint showing questions for a given page

        Returns:
            response: A json object representing questions for a given page
        """
        selection = Question.query.order_by(Question.id).all()
        current_selection = paginate_questions(request, selection)

        categories = Category.query.all()
        categories_formatted = {category.id:category.type for category in categories}

        if len(current_selection) == 0:
            abort(404)
          
        return jsonify({
            "success": True,
            "questions": current_selection,
            "total_questions": len(selection),
            "current_category": None,
            "categories": categories_formatted
        })
    
    # delete a question using id
    @app.route('/questions/<int:question_id>',  methods=['DELETE'])
    def delete_question_by_id(question_id):
        """Route handler for endpoint to delete a single question

        Args:
            question_id: An int representing the identifier for a question to
                delete

        Returns:
            response: A json object containing the id of the question that was
                deleted
        """
        question = Question.query.get(question_id)
        if question is None:
            abort(404)

        try:
            question.delete()
            selection = Question.query.order_by(Question.id).all()
            result = [item.format for item in selection]
            current_selection = paginate_questions(request, selection)
            return jsonify({
                "success": True,
                "deleted": question.id,
                "questions": current_selection,
                "total_questions": len(selection),
                "current_category": None,
            })

        except exception as e:
            error = true
            print(sys.exc_info())
            print(e)
            abort(422)
        finally:
            db.session.close()


    
    @app.route('/questions',  methods=['POST'])
    def add_question():
        error = False
        body = request.get_json()

        question = body.get("question", None)
        answer = body.get("answer", None)
        category = int(body.get("category", "1"))
        difficulty = int(body.get("difficulty", "1"))

        try:
            question = Question(question=question, answer=answer, category=category, difficulty=difficulty)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_selection = paginate_questions(request, selection)

            return jsonify({
                "success": True,
                "created": question.id,
                "questions": current_selection,
                "total_questions": len(selection),
          })

        except exception as e:
            error = true
            print(sys.exc_info())
            print(e)
            abort(422)


    
    
    @app.route('/questions/search',  methods=['POST'])
    def search_question():
      
        body = request.get_json()
        search_term = request.form.get('searchTerm', '')
       

        selection = Question.query.filter(Question.question.ilike('%{}%'.format('searchTerm'))).all()
        paginate = paginate_questions(request,selection)
        questions = [que.format() for que in selection]
         

        if(len(questions) == 0): 
              abort(400)
        
        result = {
          "success": True,
          "questions": questions,
          "totalQuestions": len(questions)
        }
        return jsonify(result)


    
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
    
        try:
            selection = Question.query.filter(Question.category == category_id).order_by(Question.id).all()
            current_selection = paginate_questions(request, selection)

            if len(current_selection) == 0:
                abort_code = 404
            else: 
                abort_code = None

            if abort_code is None:
                return jsonify({
                "success": True,
                "questions": current_selection,
                "total_questions": len(selection),
                "current_category": None,
                })

        except exception as e:
            error = true
            print(sys.exc_info())
            print(e)
            abort(422)
        finally:
            db.session.close()
        
        if abort_code:
            abort(abort_code)

    
    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        """Route handler for endpoint starting a new quiz

        Returns:
            response: A json object representing a random question given the
                specified parameters
        """
        body = request.get_json()

        previous_questions = body.get('previous_questions', [])            
        quiz_category = body.get('quiz_category', {'id': "0", 'type': "click"})
        quiz_category_id = int(quiz_category['id'])


        try:
            if quiz_category_id > 0:
                if len(previous_questions) == 0:
                    selection = Question.query.filter(Question.category == quiz_category_id).order_by(Question.id).all()
                else:
                    selection = Question.query.filter(Question.category == quiz_category_id, Question.id.notin_(previous_questions)).order_by(Question.id).all()
            else:
                if len(previous_questions) == 0:
                    selection = Question.query.order_by(Question.id).all()
                else:
                    selection = Question.query.filter(Question.id.notin_(previous_questions)).order_by(Question.id).all()

            if len(selection) == 0:
                return jsonify({
                    "success": True,
                    "question": None
                    })


            random_question = random.choice(selection).format()

            return jsonify({
              "success": True,
              "question": random_question
            })

        except Exception as e:
            error = True
            print(sys.exc_info())
            print(e)
            abort(422)

    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error_code": 400,
            "message": "bad request"
        })
        return response, 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        })
        return response, 404

    @app.errorhandler(405)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "no such method"
        })
        return response, 405


    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error_code": 422,
            "message": "unprocessable entity"
        })
        return response, 422 

    @app.errorhandler(500)
    def internal_error(error):
        
        return jsonify({
            "success": False,
            "error_code": 500,
            "message": "Internal Server Error"
        })
        return response, 500   

    return app

    