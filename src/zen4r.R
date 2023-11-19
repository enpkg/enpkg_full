# install.packages("remotes")
# require("remotes")
# install_github("eblondel/zen4R")
# install from dev branch
# install_github("eblondel/zen4R@127-zenodo-invenio-rdm")

# require("devtools")
# install_github("eblondel/atom4R")

# Docs at https://github.com/eblondel/zen4R/wiki

library(zen4R)



zenodo <- ZenodoManager$new()

ZENODO_SANDBOX_TOKEN = Sys.getenv("ZENODO_SANDBOX_TOKEN")
ZENODO_TOKEN = Sys.getenv("ZENODO_TOKEN")

zenodo <- ZenodoManager$new(
   url = "https://zenodo.org/api", #"http://sandbox.zenodo.org/api", #
   token = ZENODO_TOKEN,
   sandbox = FALSE,
   logger = "INFO"
)

my_zenodo_records <- zenodo$getDepositions()

my_rec <- zenodo$getDepositionByConceptDOI("10.5072/zenodo.209")
my_rec$getVersions()


# We go for an upload to the sandbox

myrec <- zenodo$createEmptyRecord()
# myrec <- ZenodoRecord$new()


myrec <- ZenodoRecord$new()
myrec$setTitle("LC-MS method")
myrec$setDescription("A lc-ms params file")
myrec$setUploadType("dataset")
myrec$addCreator(firstname = "Pierre-Marie", lastname = "Allard", affiliation = "University of Fribourg", orcid = "0000-0003-3389-2191")
# myrec$setLicense("cc0")
myrec$setAccessRight("open")
# myrec$setDOI("mydoi") #use this method if your DOI has been assigned elsewhere, outside Zenodo
# myrec$addCommunity("ecfunded")


# [zen4R][ERROR] ZenodoRecord - License with id 'cc0' doesn't exist in Zenodo 
# Error in myrec$setLicense("cc0") : 
#   License with id 'cc0' doesn't exist in Zenodo
# We thius check the licenses available in Zenodo

zenodo$getLicenses()



myrec$id

my_zenodo_records <- zenodo$getDepositions()


myrec <- zenodo$publishRecord(myrec$id)


ZenodoManager$getLicenses()

zenodo$getLicenses(pretty = TRUE)

zenodo$getCommunities()


zenodo$getDepositions(
q = "",
size = 10,
all_versions = FALSE,
exact = TRUE,
quiet = FALSE
)


zenodo$uploadFile("/home/allardpm/git_repos/ENPKG/enpkg_full/data/input/enpkg_toy_dataset/metadata/lcms_method_params.txt", myrec)

my_rec <- zenodo$getDepositionById(210)

my_rec$doi

#get record by DOI
myrec <- zenodo$getDepositionByConceptDOI("10.5281/zenodo.10156826")
myrec <- zenodo$getDepositionByDOI("10.5281/zenodo.10156827")
myrec <- zenodo$getDepositionByConceptDOI("10.5072/zenodo.209")


today <- Sys.Date()

# myrec <- ZenodoRecord$new()
myrec$setTitle("lc_ms_method_params")
myrec$setDescription("A lc-ms params file v2")
myrec$setUploadType("dataset")
myrec$addCreator(firstname = "Pierre-Marie", lastname = "Allard", affiliation = "University of Fribourg", orcid = "0000-0003-3389-2191")
# myrec$setLicense("cc0")
myrec$setAccessRight("open")
myrec$setPublicationDate(today)
# myrec$setDOI("mydoi") #use this method if your DOI has been assigned elsewhere, outside Zenodo
# myrec$addCommunity("ecfunded")

myrec <- zenodo$depositRecord(myrec)



myrec <- zenodo$depositRecordVersion(myrec, delete_latest_files = TRUE, files = "/home/allardpm/git_repos/ENPKG/enpkg_full/data/input/enpkg_toy_dataset/metadata/lcms_method_params.txt", publish = FALSE)


myrec <- zenodo$editRecord(myrec$id)

today <- Sys.Date()

# myrec <- ZenodoRecord$new()
myrec$setTitle("lc_ms_method_params")
myrec$setDescription("A lc-ms params file v2")
myrec$setUploadType("dataset")
myrec$addCreator(firstname = "Pierre-Marie", lastname = "Allard", affiliation = "University of Fribourg", orcid = "0000-0003-3389-2191")
# myrec$setLicense("cc0")
myrec$setAccessRight("open")
myrec$setPublicationDate(today)

myrec <- zenodo$depositRecord(myrec, publish = FALSE)

myrec <- zenodo$publishRecord(myrec$id)

