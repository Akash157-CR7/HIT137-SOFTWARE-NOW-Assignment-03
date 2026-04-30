import cv2
import random


class ImageProcessor:
    """
    This class is responsible for image processing.

    It loads the original image and creates a modified version
    with exactly 5 random differences.
    """

    def __init__(self):
        # This list will store the 5 difference areas.
        # Each difference is stored as: (x, y, width, height)
        self.difference_regions = []

    def load_image(self, image_path):
        """
        This method loads an image from the computer.
        """

        # cv2.imread reads the image using OpenCV
        image = cv2.imread(image_path)

        # If image is None, it means the image was not loaded properly
        if image is None:
            raise ValueError("Image could not be loaded. Please choose a valid image file.")

        return image

    def create_modified_image(self, original_image):
        """
        This method creates a copy of the original image
        and adds exactly 5 random differences.
        """

        # Make a copy of the original image so we can change it
        modified_image = original_image.copy()

        # Clear old differences before creating new ones
        self.difference_regions = []

        # Get the height and width of the image
        height, width, channels = original_image.shape

        # Keep creating differences until we have exactly 5
        while len(self.difference_regions) < 5:

            # Choose a random size for the difference area
            region_width = random.randint(30, 60)
            region_height = random.randint(30, 60)

            # Choose a random position for the difference.
            # We subtract the region size so the area stays inside the image.
            x = random.randint(0, width - region_width - 1)
            y = random.randint(0, height - region_height - 1)

            # Store the new difference area
            new_region = (x, y, region_width, region_height)

            # Only use the new region if it does not overlap with another difference
            if not self.is_overlapping(new_region):

                # Randomly choose what type of change to make.
                # We use three types to satisfy the assignment requirement.
                alteration_type = random.choice(["colour", "blur", "darken"])

                if alteration_type == "colour":
                    # Make the selected area slightly brighter.
                    # This creates a small colour shift difference.
                    modified_image[y:y + region_height, x:x + region_width] = cv2.add(
                        modified_image[y:y + region_height, x:x + region_width],
                        (30, 30, 30, 0)
                    )

                elif alteration_type == "blur":
                    # Blur the selected area.
                    # This creates a texture/detail difference.
                    modified_image[y:y + region_height, x:x + region_width] = cv2.GaussianBlur(
                        modified_image[y:y + region_height, x:x + region_width],
                        (15, 15),
                        0
                    )

                elif alteration_type == "darken":
                    # Make the selected area slightly darker.
                    # This creates a natural difference without drawing a bright shape.
                    modified_image[y:y + region_height, x:x + region_width] = cv2.subtract(
                        modified_image[y:y + region_height, x:x + region_width],
                        (35, 35, 35, 0)
                    )

                # Save this difference area in the list
                self.difference_regions.append(new_region)

        return modified_image, self.difference_regions

    def is_overlapping(self, new_region):
        """
        This method checks if a new difference area overlaps
        with any existing difference area.
        """

        x1, y1, width1, height1 = new_region

        # Go through each existing difference region
        for region in self.difference_regions:
            x2, y2, width2, height2 = region

            # Check if the two rectangles are separate
            is_separate = (
                x1 + width1 < x2 or
                x1 > x2 + width2 or
                y1 + height1 < y2 or
                y1 > y2 + height2
            )

            # If they are not separate, then they are overlapping
            if not is_separate:
                return True

        # If no overlap is found, return False
        return False