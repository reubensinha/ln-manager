import { useEffect, useState } from "react";
import { Text, Divider } from "@mantine/core";
import { useParams } from "react-router";

import { getBookByID } from "../api/api";
import {
  type BookItem,
} from "../types/CardItems";
import BookInfo from "../components/BookInfo";

function Book() {
  const { bookID } = useParams<{ bookID: string }>();
  const [book, setBook] = useState<BookItem | null>(null);

  useEffect(() => {
    if (bookID) {
      getBookByID(bookID).then((data) => {
        setBook(data);
      });
    }
  }, [bookID]);

  if (!book) {
    return <Text>Loading book...</Text>;
  }

  return (
    <>
      <BookInfo book={book} />
      <Divider my="xl" />
      <Text>TODO: Insert Releases</Text>
    </>
  );
}

export default Book;
