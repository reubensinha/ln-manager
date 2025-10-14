import { Modal } from "@mantine/core";
import BookPage from "../../pages/BookPage";

function BookPageModal({
  bookID,
  open,
  onClose,
}: {
  bookID: string;
  open: boolean;
  onClose: () => void;
}) {
  return (
    <Modal 
      opened={open} 
      onClose={onClose} 
      title="Book Details" 
      size="xl"
      styles={{
        body: {
          maxHeight: '80vh',
          overflow: 'auto',
        }
      }}
    >
      <BookPage bookID={bookID} />
    </Modal>
  );
}

export default BookPageModal;