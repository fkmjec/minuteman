# Specification - A tool for automatically creating meeting minutes
    * working name: Minuteman
    * UI inspired by Charles Translator

# Web app
## what pages should there be?
    * an index page with the tool (for model testing, later, it will be hopefully embedded in google docs or shared in some way)
    * an about page for info on the project
## what features should it have
### high-level
    * user input resembling the one found on Charles Translator
        * reasonably fast reloads on transcript change
    * API for use in Google docs with live transcripts
    * data collection for debugging models

## stack
    * hedgedoc - rozšíření
        * je to opensource
    * jitsi meet? to je taky opensource
        * udělat z toho dohromady nějakou spletenost, zahodit obraz?
    * Flask
    * SqlAlchemy
    * WTForms
    * FrontEnd - hopefully just vanilla JS, nothing fancy
        * React?
    * TorchServe for serving (much easier getting the transformers to work)

## current TODO
    * implement a simple flask backend
    * pick a frontend framework, design the UI
    * dockerize the whole thing, write Dockerfiles for both tf-serving and the backend
    * implement an API
