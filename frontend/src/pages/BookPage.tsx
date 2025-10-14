import { useEffect, useState } from "react";
import { Text, Divider } from "@mantine/core";
import { useParams } from "react-router";

import { getBookByID } from "../api/api";
import BookInfo from "../components/BookInfo";
import { type Book } from "../api/ApiResponse";
import ReleasesTable from "../components/ReleasesTable";

function BookPage({ bookID: propBookID }: { bookID?: string }) {
  const { bookID: paramBookID } = useParams<{ bookID: string }>();
  const bookID = propBookID || paramBookID;

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
      <ReleasesTable releases={book.releases ? book.releases : []} />
    </>
  );
}

export default BookPage;
