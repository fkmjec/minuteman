# Specification - A tool for automatically creating meeting minutes
    * working name: Minuteman
    * UI inspired by Charles Translator

# Web app
## what pages should there be?
    * an index page with the tool (for model testing, later, it will be hopefully embedded in google docs or shared in some way)
    * an about page for info on the project
## what features should it have
    * model execution (on a GPU, CPU is way too slow) 
        * using tensorflow serving, for examples, look at 
    * data logging (together with timestamps, as this will help with debugging the model)
    * form input, obviously
    * live updates without reload, obviously
    * reasonably fast (>1s overhead on an update)

## stack
    * Flask
    * SqlAlchemy
    * WTForms
    * FrontEnd - hopefully just vanilla JS, nothing fancy
        * React?
    * Tensorflow Serving
    * Tensor2Tensor for requests to backend
        * https://github.com/ufal/lindat-translation/blob/master/app/models/t2t_model.py, line with "_do_send_request"

## current TODO
    * implement a simple flask backend
    * write the form for input
    * implement the API
