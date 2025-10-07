import { useEffect, useState } from "react";
import { Text, Divider } from "@mantine/core";
import { useParams } from "react-router";

import { getBookByID } from "../api/api";
import BookInfo from "../components/BookInfo";
import { type Book } from "../api/ApiResponse";

function Book() {
  const { bookID } = useParams<{ bookID: string }>();
  const [book, setBook] = useState<Book | null>(null);

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
