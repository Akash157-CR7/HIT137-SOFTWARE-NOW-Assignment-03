class DifferenceGame:
    """
    This class handles the main game logic.

    It checks if the player's click is correct or incorrect.
    It also keeps track of found differences, remaining differences,
    and mistakes.
    """

    def __init__(self):
        # This list stores all 5 difference areas
        self.difference_regions = []

        # This list stores the differences that the player has already found
        self.found_regions = []

        # This keeps count of wrong clicks
        self.mistakes = 0

        # The player is allowed only 3 mistakes for each image
        self.max_mistakes = 3

    def start_new_game(self, difference_regions):
        """
        This method starts or restarts the game for a new image.
        """

        # Store the 5 differences created by the image processor
        self.difference_regions = difference_regions

        # Clear previously found differences
        self.found_regions = []

        # Reset mistakes to 0 for the new image
        self.mistakes = 0

    def check_click(self, click_x, click_y):
        """
        This method checks whether the player clicked on a difference.

        It returns:
        - "correct" if the click is on an unfound difference
        - "already_found" if the difference was already found before
        - "wrong" if the click is not on any difference
        - "game_over" if the player has already made 3 mistakes
        """

        # If the player already made 3 mistakes, stop checking
        if self.mistakes >= self.max_mistakes:
            return "game_over", None

        # Check each difference region
        for region in self.difference_regions:
            x, y, width, height = region

            # Check if the click is inside this difference area
            clicked_inside = (
                x <= click_x <= x + width and
                y <= click_y <= y + height
            )

            if clicked_inside:
                # If this region was already found, do not count it again
                if region in self.found_regions:
                    return "already_found", region

                # Save the region as found
                self.found_regions.append(region)
                return "correct", region

        # If the click is not inside any difference area, it is a mistake
        self.mistakes += 1

        # If mistakes reached 3, the game is over for this image
        if self.mistakes >= self.max_mistakes:
            return "game_over", None

        return "wrong", None

    def get_remaining_count(self):
        """
        This method returns how many differences are still not found.
        """

        return len(self.difference_regions) - len(self.found_regions)

    def get_mistake_count(self):
        """
        This method returns the current number of mistakes.
        """

        return self.mistakes

    def get_unfound_regions(self):
        """
        This method returns all differences that have not been found yet.
        This will be used by the reveal button.
        """

        unfound_regions = []

        for region in self.difference_regions:
            if region not in self.found_regions:
                unfound_regions.append(region)

        return unfound_regions

    def is_completed(self):
        """
        This method checks if the player found all 5 differences.
        """

        return self.get_remaining_count() == 0