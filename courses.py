
class AvailableCourses:
    def __init__(self):
        self.available_courses = {
            "20-3001": "BLS Provider",
            "20-3002": "Heartsaver First Aid CPR AED",
            "20-3004": "Heartsaver CPR AED",
            "20-3005": "Heartsaver First Aid",
            "20-3011": "Heartsaver for K-12 Schools",
            "20-3016": "BLS Instructor",
            "20-3018": "Advisor: BLS"
        }

    def is_course_available(self, product_code):
        return product_code in self.available_courses

    def course_name_on_eCard(self, product_code):
        return self.available_courses.get(product_code)
