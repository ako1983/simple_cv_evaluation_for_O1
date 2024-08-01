from fpdf import FPDF
import shutil
import os

# Define the directory for saving the PDFs
output_directory = "cv"

# Create the directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)
# Define a class for creating the PDF CVs
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Curriculum Vitae', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

# Sample data for the fake CVs
cv_data = [
    {
        "title": "fake_CV_1 for test",
        "body": "John Doe is a world-renowned physicist with numerous accolades including the Nobel Prize in Physics. "
                "He has published over 200 peer-reviewed papers, served as a lead editor for several top-tier journals, "
                "and has been invited to deliver keynote speeches at major international conferences. He has also mentored "
                "a significant number of PhD students who have gone on to have successful careers in academia and industry."
    },
    {
        "title": "fake_CV_2 for test",
        "body": "Jane Smith is an accomplished artist known for her innovative use of digital media. She has exhibited "
                "her work in prestigious galleries around the world, and her pieces are part of several major museum collections. "
                "She has been featured in prominent art magazines and has received numerous awards, including the Turner Prize."
    },
    {
        "title": "fake_CV_3 for test",
        "body": "Dr. Alex Johnson is a pioneering researcher in artificial intelligence and machine learning. He has been "
                "the principal investigator on several high-profile projects funded by the National Science Foundation and DARPA. "
                "He has authored over 150 research papers and holds multiple patents in AI technologies. He regularly consults "
                "for leading tech companies and government agencies."
    },
    {
        "title": "fake_CV_4 for test",
        "body": "Maria Gonzalez is a celebrated conductor and composer. She has led some of the world's most renowned orchestras "
                "and her compositions have been performed internationally. She has won numerous prestigious awards in classical music, "
                "including the Grammy Award for Best Classical Composition. She also serves as a professor of music at a top conservatory."
    },
    {
        "title": "fake_CV_5 for test",
        "body": "David Lee is a distinguished scholar in the field of economics. He has served as a senior advisor to several "
                "governments and international organizations. He has authored influential books and papers that have shaped economic "
                "policy worldwide. He is a frequent keynote speaker at global economic forums and has received numerous honors for his work."
    },
    {
        "title": "fake_CV_6 for test",
        "body": "Emma Brown is a rising star in the world of fashion design. She has launched her own successful clothing line and "
                "has been featured in major fashion magazines. However, her experience is primarily limited to local fashion shows and "
                "she has yet to make a significant impact internationally. She has potential but lacks a track record of sustained acclaim."
    },
    {
        "title": "fake_CV_7 for test",
        "body": "Michael Davis is an innovative software developer with several successful apps to his name. While he has a strong "
                "following in niche tech communities, he has not yet achieved widespread recognition. His work is promising but he "
                "lacks major awards or significant contributions to major projects in the industry."
    },
    {
        "title": "fake_CV_8 for test",
        "body": "Olivia Taylor is a talented chef known for her creative fusion cuisine. She has worked at several renowned restaurants "
                "and has been a finalist in a few culinary competitions. However, she has not yet established a strong enough reputation "
                "to be considered an industry leader. Her career is on an upward trajectory but she is not yet at the top of her field."
    },
    {
        "title": "fake_CV_9 for test",
        "body": "James Wilson has some experience in the music industry, having released a few independent albums. However, he has not "
                "achieved significant recognition or commercial success. He has not received any major awards and his music has not been "
                "featured in prominent venues or media. His portfolio lacks the achievements necessary to qualify for an O1 visa."
    },
    {
        "title": "fake_CV_10 for test",
        "body": "Laura Martin has written a few articles for local magazines and has been a guest speaker at small community events. "
                "She has not published any major works or received recognition from established institutions. Her achievements do not meet "
                "the high standards required for an O1 visa, as she lacks evidence of extraordinary ability or acclaim."
    }
]

# Create the PDF documents
for i, cv in enumerate(cv_data, start=1):
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_title(cv['title'])
    pdf.chapter_body(cv['body'])
    pdf.output(f"/mnt/data/fake_CV_{i}_for_test.pdf")

# Create a ZIP archive of all the generated PDFs
shutil.make_archive(output_directory, 'zip', output_directory)