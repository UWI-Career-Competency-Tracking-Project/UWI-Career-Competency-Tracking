from App.database import db

class Workshop(db.Model):
    __tablename__ = 'workshops'
    
    workshopID = db.Column(db.String(20), primary_key=True)
    workshopName = db.Column(db.String(100), nullable=False)
    workshopDescription = db.Column(db.Text, nullable=False)
    workshopDate = db.Column(db.Date, nullable=False)
    workshopTime = db.Column(db.Time, nullable=False)
    instructor = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False) 