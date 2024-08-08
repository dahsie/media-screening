import logging


def create_logger(name, file_name : str):
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create a file handle
    file_handler = logging.FileHandler(file_name)
    file_handler.setLevel(logging.INFO)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] -- [%(funcName)s()] : %(message)s')
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)
    
    return logger
    
logger = create_logger(__name__, 'utils.log')

def display(x: list, y: list, ax, label: str, xlabel : str, ylabel: str, title = None) :
    ax.plot(x, y, label=label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    if title is not None:
        ax.set_title(title)

def split_liste(texts : list[str], limit : int , separators: list[str] = ['.', '!', '?', '\n', '\n\n'])-> list[list[str]]:
        """
        Splits a list of texts into sub-lists based on a token limit.

        Args:
            texts (list[str]): The texts to split.
            limit (int): The token limit.
            separators (list[str]): The list of separators to use for splitting. Defaults to ['.', '!', '?', '\n', '\n\n'].

        Returns:
            list[list[str]]: The split texts.

        Raises:
            ValueError: If a single text exceeds the token limit.
        """
        logger.info("Splitting texts into sub-lists with a limit of %d tokens", limit)
        
        sub_list = []
        liste = []
        cpt = 0
        for text in texts :
            length_text = len(text)

            if length_text > limit :
                pos = limit
            
                while pos > 0 and text[pos] not in separators:
                    pos -= 1
                pos += 1 #One include the ponctuation sign within the sub-string
                text = text[:pos]
                logger.warning(f"The text has {length_text} tokens, which exceeds the limit of {limit} tokens. It is troncated to {len(text)} token")

            else :
                cpt += length_text

                if cpt < limit:
                    sub_list.append(text)

                else :
                    liste.append(sub_list)
                    cpt, sub_list = length_text, []
                    sub_list.append(text)

        liste.append(sub_list)
        logger.info("Texts successfully split into sub-lists.")
        return liste