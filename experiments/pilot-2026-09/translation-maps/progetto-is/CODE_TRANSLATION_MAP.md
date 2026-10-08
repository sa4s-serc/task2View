# Code Translation Map

This map documents the standalone English migration. The English variant intentionally changes source identifiers, APIs, JSON contracts, persistence names, internal values, and web routes; it is not compatible with the Italian original.

## Application

| Italian | English | Notes |
|---|---|---|
| `BibliotecaFacade` | `LibraryFacade` |  |
| `GestoreNotifiche` | `NotificationManager` |  |
| `GestorePersistenza` | `PersistenceManager` |  |
| `GestorePrenotazioni` | `ReservationManager` |  |
| `GestoreSale` | `StudyRoomManager` |  |
| `GestoreUtenti` | `UserManager` |  |
| `PrenotazioniApplication` | `ReservationsApplication` |  |
| `ServizioNotifiche` | `NotificationService` |  |

## Client

| Italian | English | Notes |
|---|---|---|
| `formattaStato` | `formatStatus` |  |
| `getUtente` | `getUser` |  |
| `mostraErrore` | `showError` |  |
| `richiediRuolo` | `requireRole` |  |
| `salvaUtente` | `saveUser` |  |
| `utente` | `user` |  |

## Controller

| Italian | English | Notes |
|---|---|---|
| `BoundaryAutenticazione` | `AuthenticationController` |  |
| `BoundaryMonitoraggio` | `MonitoringController` |  |
| `BoundaryPrenotazione` | `ReservationController` |  |
| `BoundarySalaStudio` | `StudyRoomController` |  |
| `BoundaryStudente` | `StudentController` |  |
| `GestoreEccezioni` | `RestExceptionHandler` |  |

## Database

| Italian | English | Notes |
|---|---|---|
| `attiva` | `active` |  |
| `prenotazione` | `reservation` |  |
| `prenotazioniPU` | `reservationsPU` |  |
| `prenotazionidb` | `reservationsdb` |  |
| `prenotazionidb_test` | `reservationsdb_test` |  |
| `reminder_inviato` | `reminder_sent` |  |
| `stato` | `status` |  |

## Dto

| Italian | English | Notes |
|---|---|---|
| `AreaDettaglioDTO` | `AreaDetailDTO` |  |
| `CreazioneSalaDTO` | `StudyRoomCreationDTO` |  |
| `DettaglioSalaDTO` | `RoomDetailDTO` |  |
| `FasciaDisponibileDTO` | `AvailableTimeSlotDTO` |  |
| `PostazioneDTO` | `SeatDTO` |  |
| `PrenotazioneDTO` | `ReservationDTO` |  |
| `RichiestaPrenotazioneDTO` | `ReservationRequestDTO` |  |
| `SalaMonitoraggioDTO` | `RoomMonitoringDTO` |  |
| `SalaStudioDTO` | `StudyRoomDTO` |  |
| `StatisticheDTO` | `StatisticsDTO` |  |
| `UtenteDTO` | `UserDTO` |  |

## Entity

| Italian | English | Notes |
|---|---|---|
| `Bibliotecario` | `Librarian` |  |
| `FasciaOraria` | `TimeSlot` |  |
| `Postazione` | `Seat` |  |
| `Prenotazione` | `Reservation` |  |
| `RegistroPrenotazioni` | `ReservationRegistry` |  |
| `RegistroSale` | `StudyRoomRegistry` |  |
| `RegistroUtenti` | `UserRegistry` |  |
| `SalaStudio` | `StudyRoom` |  |
| `StatoEnum` | `StatusEnum` |  |
| `Studente` | `Student` |  |
| `Utente` | `User` |  |

## File

| Italian | English | Notes |
|---|---|---|
| `AreaDettaglioDTO.java` | `AreaDetailDTO.java` | Public Java type filename |
| `BibliotecaFacade.java` | `LibraryFacade.java` | Public Java type filename |
| `Bibliotecario.java` | `Librarian.java` | Public Java type filename |
| `BoundaryAutenticazione.java` | `AuthenticationController.java` | Public Java type filename |
| `BoundaryMonitoraggio.java` | `MonitoringController.java` | Public Java type filename |
| `BoundaryPrenotazione.java` | `ReservationController.java` | Public Java type filename |
| `BoundarySalaStudio.java` | `StudyRoomController.java` | Public Java type filename |
| `BoundaryStudente.java` | `StudentController.java` | Public Java type filename |
| `CreazioneSalaDTO.java` | `StudyRoomCreationDTO.java` | Public Java type filename |
| `DettaglioSalaDTO.java` | `RoomDetailDTO.java` | Public Java type filename |
| `FasciaDisponibileDTO.java` | `AvailableTimeSlotDTO.java` | Public Java type filename |
| `FasciaOraria.java` | `TimeSlot.java` | Public Java type filename |
| `GestoreEccezioni.java` | `RestExceptionHandler.java` | Public Java type filename |
| `GestoreNotifiche.java` | `NotificationManager.java` | Public Java type filename |
| `GestorePersistenza.java` | `PersistenceManager.java` | Public Java type filename |
| `GestorePrenotazioni.java` | `ReservationManager.java` | Public Java type filename |
| `GestoreSale.java` | `StudyRoomManager.java` | Public Java type filename |
| `GestoreUtenti.java` | `UserManager.java` | Public Java type filename |
| `Postazione.java` | `Seat.java` | Public Java type filename |
| `PostazioneDTO.java` | `SeatDTO.java` | Public Java type filename |
| `Prenotazione.java` | `Reservation.java` | Public Java type filename |
| `PrenotazioneDTO.java` | `ReservationDTO.java` | Public Java type filename |
| `PrenotazioniApplication.java` | `ReservationsApplication.java` | Public Java type filename |
| `RegistroPrenotazioni.java` | `ReservationRegistry.java` | Public Java type filename |
| `RegistroSale.java` | `StudyRoomRegistry.java` | Public Java type filename |
| `RegistroUtenti.java` | `UserRegistry.java` | Public Java type filename |
| `RichiestaPrenotazioneDTO.java` | `ReservationRequestDTO.java` | Public Java type filename |
| `SalaMonitoraggioDTO.java` | `RoomMonitoringDTO.java` | Public Java type filename |
| `SalaStudio.java` | `StudyRoom.java` | Public Java type filename |
| `SalaStudioDTO.java` | `StudyRoomDTO.java` | Public Java type filename |
| `ServizioNotifiche.java` | `NotificationService.java` | Public Java type filename |
| `StatisticheDTO.java` | `StatisticsDTO.java` | Public Java type filename |
| `StatoEnum.java` | `StatusEnum.java` | Public Java type filename |
| `Studente.java` | `Student.java` | Public Java type filename |
| `Utente.java` | `User.java` | Public Java type filename |
| `UtenteDTO.java` | `UserDTO.java` | Public Java type filename |
| `crea-sala.html` | `create-room.html` | Static web page |
| `dashboard-bibliotecario.html` | `librarian-dashboard.html` | Static web page |
| `dashboard-studente.html` | `student-dashboard.html` | Static web page |
| `prenotazione.html` | `reservation.html` | Static web page |
| `registrazione.html` | `registration.html` | Static web page |

## Identifier

| Italian | English | Notes |
|---|---|---|
| `.scaduta` | `.expired` |  |
| `ANNULLATA` | `CANCELLED` |  |
| `ASSEGNAZIONE_AUTOMATICA` | `AUTO_ASSIGNMENT` |  |
| `AdapterServizioNotifiche` | `NotificationServiceAdapter` |  |
| `AnnullaPrenotazioneTest` | `CancelReservationTest` |  |
| `AnnullaReservation` | `CancelReservation` |  |
| `AssegnazionePrimaLibera` | `FirstAvailableAssignment` |  |
| `AutenticazioneTest` | `AuthenticationTest` |  |
| `BIBLIOTECARIO` | `LIBRARIAN` |  |
| `BibliotecaFacade` | `LibraryFacade` |  |
| `Bibliotecario` | `Librarian` |  |
| `BibliotecarioFactory` | `LibrarianFactory` |  |
| `BoundaryAutenticazione` | `AuthenticationController` |  |
| `BoundaryPrenotazione` | `ReservationController` |  |
| `BoundarySalaStudio` | `StudyRoomController` |  |
| `BoundaryStudente` | `StudentController` |  |
| `CONCLUSA` | `COMPLETED` |  |
| `CONFERMATA` | `CONFIRMED` |  |
| `CardPrenotazione` | `ReservationCard` |  |
| `CardSala` | `RoomCard` |  |
| `Codice` | `Code` |  |
| `ConfigurazioneNotifiche` | `NotificationConfiguration` |  |
| `ConsultazioneSaleDisponibiliTest` | `AvailableStudyRoomsQueryTest` |  |
| `CreaSala` | `CreateRoom` |  |
| `CreaSalaStudioTest` | `CreateStudyRoomTest` |  |
| `CreazioneSalaDTO` | `StudyRoomCreationDTO` |  |
| `DashboardBibliotecario` | `LibrarianDashboard` |  |
| `DashboardStudente` | `StudentDashboard` |  |
| `Descrizione` | `Description` |  |
| `DettaglioSalaDTO` | `RoomDetailDTO` |  |
| `EffettuaPrenotazioneTest` | `MakeReservationTest` |  |
| `EliminaSalaStudioTest` | `DeleteStudyRoomTest` |  |
| `Fascia` | `TimeSlot` |  |
| `FasciaDisponibileDTO` | `AvailableTimeSlotDTO` |  |
| `FasciaOraria` | `TimeSlot` |  |
| `GestioneBiblioteca` | `library-reservation-system` |  |
| `GestisciTerminePrenotazioneTest` | `ManageReservationEndTest` |  |
| `GestoreEccezioni` | `RestExceptionHandler` |  |
| `GestoreNotifiche` | `NotificationManager` |  |
| `GestorePersistenza` | `PersistenceManager` |  |
| `GestorePrenotazioni` | `ReservationManager` |  |
| `GestoreSale` | `StudyRoomManager` |  |
| `GestoreUtenti` | `UserManager` |  |
| `Identificativo` | `Identifier` |  |
| `MATRICOLA` | `STUDENT_NUMBER` |  |
| `Nome` | `Name` |  |
| `NonConfermate` | `Unconfirmed` |  |
| `Notificationtion` | `Notification` |  |
| `Orario` | `WorkingHours` |  |
| `PLACEHOLDER_CODICE` | `IDENTIFIER_PLACEHOLDER` |  |
| `PLACEHOLDER_COGNOME` | `SURNAME_PLACEHOLDER` |  |
| `PLACEHOLDER_NOME` | `NAME_PLACEHOLDER` |  |
| `Postazione` | `Seat` |  |
| `PostazioneDTO` | `SeatDTO` |  |
| `Postazioni` | `Seats` |  |
| `Posti` | `Seats` |  |
| `Prenotazione` | `Reservation` |  |
| `PrenotazioneConfermata` | `ReservationConfirmed` |  |
| `PrenotazioneDTO` | `ReservationDTO` |  |
| `Prenotazioni` | `Reservations` |  |
| `PrenotazioniApplication` | `ReservationsApplication` |  |
| `Registrati` | `Register` |  |
| `Registrazione` | `Registration` |  |
| `RegistrazioneTest` | `RegistrationTest` |  |
| `RegistroPrenotazioni` | `ReservationRegistry` |  |
| `RegistroSale` | `StudyRoomRegistry` |  |
| `RegistroUtenti` | `UserRegistry` |  |
| `RichiestaPrenotazioneDTO` | `ReservationRequestDTO` |  |
| `RiepilogoPrenotazione` | `ReservationSummary` |  |
| `Ruolo` | `Role` |  |
| `SCADUTA` | `EXPIRED` |  |
| `STUDENTE` | `STUDENT` |  |
| `Sala` | `Room` |  |
| `SalaMonitoraggioDTO` | `RoomMonitoringDTO` |  |
| `SalaStudio` | `StudyRoom` |  |
| `SalaStudioDTO` | `StudyRoomDTO` |  |
| `SchedulerNotifiche` | `NotificationScheduler` |  |
| `SelezionaArea` | `AreaSelection` |  |
| `SelezionaDataAndSala` | `DateAndRoomSelection` |  |
| `SelezionaFascia` | `TimeSlotSelection` |  |
| `SelezionaPostazione` | `SeatSelection` |  |
| `ServizioNotifiche` | `NotificationService` |  |
| `StatoAnnullata` | `CancelledState` |  |
| `StatoConclusa` | `CompletedState` |  |
| `StatoConfermata` | `ConfirmedState` |  |
| `StatoPrenotazione` | `ReservationState` |  |
| `StatoScaduta` | `ExpiredState` |  |
| `StrategiaAssegnazione` | `AssignmentStrategy` |  |
| `Studente` | `Student` |  |
| `StudenteFactory` | `StudentFactory` |  |
| `TOLLERANZA_ANNULLAMENTO_ORE` | `CANCELLATION_DEADLINE_HOURS` |  |
| `Utente` | `User` |  |
| `UtenteDTO` | `UserDTO` |  |
| `UtenteFactory` | `UserFactory` |  |
| `addFascia` | `addTimeSlot` |  |
| `addOrarioLavorativo` | `addWorkingHours` |  |
| `aggiorna` | `update` |  |
| `aggiornaRiepilogo` | `updateSummary` |  |
| `aggiornaSala` | `updateRoom` |  |
| `aggiornaSale` | `updateRooms` |  |
| `aggiornaStatistiche` | `updateStatistics` |  |
| `aggiungiArea` | `addArea` |  |
| `annulla` | `cancel` |  |
| `annullaPrenotazione` | `cancelReservation` |  |
| `aperturaGiorno` | `dayOpening` |  |
| `apriDashboard` | `openDashboard` |  |
| `apriLogin` | `openLogin` |  |
| `areaSelezionata` | `selectedArea` |  |
| `assegnazionePrimaLibera` | `firstAvailableAssignment` |  |
| `autenticazione` | `authenticate` |  |
| `bibliotecaFacade` | `libraryFacade` |  |
| `bibliotecario` | `librarian` |  |
| `bottoneSelezionato` | `selectedButton` |  |
| `btnAggiorna` | `refreshButton` |  |
| `btnAnnulla` | `cancelButton` |  |
| `buttonRegistrati` | `registerButton` |  |
| `calcolaStatisticheSala` | `calculateRoomStatistics` |  |
| `campo` | `field` |  |
| `campoPosti` | `seatCountField` |  |
| `campoPosti` | `seatField` |  |
| `cardPosti` | `seatCard` |  |
| `cardSala` | `roomCard` |  |
| `cercaLibrarianPerCodice` | `findLibrarianByCode` |  |
| `cercaPerCampi` | `findByFields` |  |
| `cercaPerCampo` | `findByField` |  |
| `cercaPrenotazioniPerSalaEData` | `findReservationsByRoomAndDate` |  |
| `cercaPrenotazioniPerStudent` | `findReservationsByStudent` |  |
| `cercaPrimoPerCampi` | `findFirstByFields` |  |
| `cercaReservationAttiva` | `findActiveReservations` |  |
| `cercaReservationsPerSeat` | `findReservationsBySeat` |  |
| `cercaSalaPerId` | `findRoomById` |  |
| `cercaStudentPerMatricola` | `findStudentByStudentNumber` |  |
| `cercaTuttePerSala` | `findAllByRoom` |  |
| `cercaUserPerEmail` | `findUserByEmail` |  |
| `chiusuraGiorno` | `dayClosing` |  |
| `codice` | `code` |  |
| `codiceIdentificativoInterno` | `internalIdentifierCode` |  |
| `cognome` | `surname` |  |
| `comboRuolo` | `roleComboBox` |  |
| `configura` | `configure` |  |
| `configuraAree` | `configureAreas` |  |
| `configuraOrariESlot` | `configureHoursAndSlots` |  |
| `configuraRadioCard` | `configureRadioCard` |  |
| `consultaSaleDisponibili` | `getAvailableStudyRooms` |  |
| `consultaStoricoPrenotazioni` | `getReservationHistory` |  |
| `consultazioneSaleDisponibili` | `getAvailableStudyRooms` |  |
| `contaPostiDisponibili` | `countAvailableSeats` |  |
| `creaSalaForm` | `createRoomForm` |  |
| `creaSalaStudio` | `createStudyRoom` |  |
| `createESalva` | `createAndSave` |  |
| `createMappaStatoPostazioni` | `createSeatStatusMap` |  |
| `criticalAnnullaReservation` | `forceCancelReservation` |  |
| `dataFutura` | `futureDate` |  |
| `dataOggi` | `today` |  |
| `dataPassata` | `pastDate` |  |
| `dataPrenotazione` | `reservationDate` |  |
| `descrizione` | `description` |  |
| `descrizioneSala` | `roomDescription` |  |
| `destinatari` | `recipients` |  |
| `dettaglioSala` | `roomDetail` |  |
| `disponibilita` | `isAvailable` |  |
| `effettuaPrenotazione` | `makeReservation` |  |
| `elimina` | `deleteRoom` |  |
| `eliminaSalaStudio` | `deleteStudyRoom` |  |
| `errore` | `error` |  |
| `etichetta` | `label` |  |
| `etichettaFascia` | `timeSlotLabel` |  |
| `fasceDisponibili` | `availableTimeSlots` |  |
| `fascia` | `timeSlot` |  |
| `fieldIdentificativo` | `identifierField` |  |
| `fieldNome` | `nameField` |  |
| `gestisciRichiestaNonValida` | `handleInvalidRequest` |  |
| `gestisciTerminePrenotazione` | `manageReservationEnd` |  |
| `gestisciTerminePrenotazioni` | `manageReservationEnd` |  |
| `gestoreNotifiche` | `notificationManager` |  |
| `gestorePersistenza` | `persistenceManager` |  |
| `gestorePrenotazioni` | `reservationManager` |  |
| `gestoreSale` | `studyRoomManager` |  |
| `gestoreUtenti` | `userManager` |  |
| `getAreePerSala` | `getAreasForRoom` |  |
| `getCodiceIdentificativoInterno` | `getInternalIdentifierCode` |  |
| `getCognome` | `getSurname` |  |
| `getDescrizione` | `getDescription` |  |
| `getDisponibile` | `isAvailable` |  |
| `getEtichetta` | `getLabel` |  |
| `getEtichettaFascia` | `getTimeSlotLabel` |  |
| `getFasceDisponibili` | `getAvailableTimeSlots` |  |
| `getFasceOrarie` | `getTimeSlots` |  |
| `getFasceOrariePrestabilite` | `getScheduledTimeSlots` |  |
| `getFascePerSala` | `getTimeSlotsForRoom` |  |
| `getIdFascia` | `getTimeSlotId` |  |
| `getIdPostazione` | `getSeatId` |  |
| `getIdSala` | `getRoomId` |  |
| `getIdStudent` | `getStudentId` |  |
| `getIdStudente` | `getStudentId` |  |
| `getIdentificativo` | `getIdentifier` |  |
| `getMatricola` | `getStudentNumber` |  |
| `getNome` | `getName` |  |
| `getNomeSala` | `getRoomName` |  |
| `getNumero` | `getNumber` |  |
| `getNumeroPostazioni` | `getSeatCount` |  |
| `getNumeroPostazioniTotali` | `getTotalSeatCount` |  |
| `getNumeroTotaleAccessi` | `getTotalVisitCount` |  |
| `getOrariApertura` | `getOpeningTimes` |  |
| `getOrariChiusura` | `getClosingTimes` |  |
| `getOrariLavorativiPerSala` | `getWorkingHoursForRoom` |  |
| `getOrarioLavorativoPerData` | `getWorkingHoursForDate` |  |
| `getPostazioni` | `getSeats` |  |
| `getPostazioniAree` | `getAreaSeatCounts` |  |
| `getPostazioniDisponibili` | `getAvailableSeats` |  |
| `getPostazioniPerArea` | `getSeatsForArea` |  |
| `getPostiAttivi` | `getActiveSeats` |  |
| `getPostiConfermati` | `getConfirmedSeats` |  |
| `getPostiDisponibili` | `getAvailableSeatCount` |  |
| `getPostiLiberi` | `getAvailableSeats` |  |
| `getPrenotazioni` | `getReservations` |  |
| `getPrenotazioniInScadenza` | `getEndingReservations` |  |
| `getPrenotazioniNonConfermate` | `getUnconfirmedReservations` |  |
| `getPrenotazioniOggi` | `getReservationsToday` |  |
| `getRuolo` | `getRole` |  |
| `getSaleDisponibili` | `getAvailableRooms` |  |
| `getTipologia` | `getType` |  |
| `getTipologiaArea` | `getAreaType` |  |
| `getTipologie` | `getTypes` |  |
| `getUtente` | `getUser` |  |
| `giorno` | `day` |  |
| `grigliaPostazioni` | `seatGrid` |  |
| `grigliaPrenotazioni` | `reservationGrid` |  |
| `idFascia` | `timeSlotId` |  |
| `idPostazione` | `seatId` |  |
| `idPrenotazione` | `reservationId` |  |
| `idSala` | `roomId` |  |
| `idSalaStudio` | `studyRoomId` |  |
| `idStudente` | `studentId` |  |
| `identificativo` | `identifier` |  |
| `identificativoProfilo` | `profileIdentifier` |  |
| `indiceGiorno` | `dayIndex` |  |
| `inviaNotifica` | `sendNotification` |  |
| `inviaPromemoria` | `sendReminders` |  |
| `isDisponibile` | `isAvailable` |  |
| `isPromemoriaInviato` | `isReminderSent` |  |
| `it.unina.prenotazioni` | `it.unina.reservations` |  |
| `lblDescrizione` | `descriptionLabel` |  |
| `lblPillNonConfermate` | `unconfirmedPillLabel` |  |
| `lblPillPostazioni` | `seatsPillLabel` |  |
| `lblPillPrenotazioni` | `reservationsPillLabel` |  |
| `lblValoreFascia` | `timeSlotValueLabel` |  |
| `lblValoreSala` | `roomValueLabel` |  |
| `lblVoceFascia` | `timeSlotFieldLabel` |  |
| `lblVoceSala` | `roomFieldLabel` |  |
| `listaPrenotazioni` | `reservationList` |  |
| `matricola` | `studentNumber` |  |
| `messaggio` | `message` |  |
| `mostraErrore` | `showError` |  |
| `nome` | `name` |  |
| `nomeLungo` | `longName` |  |
| `nomeSala` | `roomName` |  |
| `nonConfermate` | `unconfirmedReservations` |  |
| `notifica` | `notification` |  |
| `notification(Reservation` | `notifyReservation(Reservation` |  |
| `notification(reservation)` | `notifyReservation(reservation)` |  |
| `notificationno` | `notify` |  |
| `notifiche` | `notifications` |  |
| `numAssegnate` | `assignedCount` |  |
| `numPostazioni` | `seatAmount` |  |
| `numero` | `number` |  |
| `numeroAree` | `areaCount` |  |
| `numeroPostazioni` | `seatCount` |  |
| `numeroPostazioniTotali` | `totalSeatCount` |  |
| `numeroTotaleAccessi` | `totalVisitCount` |  |
| `orariApertura` | `openingTimes` |  |
| `orariChiusura` | `closingTimes` |  |
| `orariContainer` | `hoursContainer` |  |
| `orariLavorativi` | `workingHours` |  |
| `orario` | `time` |  |
| `orarioApertura` | `openingTime` |  |
| `orarioChiusura` | `closingTime` |  |
| `panelPosti` | `seatsPanel` |  |
| `pannelloRiepilogo` | `summaryPanel` |  |
| `parseOrario` | `parseTime` |  |
| `postazione` | `seat` |  |
| `postazioni` | `seats` |  |
| `postazioniAree` | `areaSeatCounts` |  |
| `postazioniOccupateOggi` | `occupiedSeatsToday` |  |
| `postazioniTotali` | `totalSeats` |  |
| `posti` | `seatCounts` |  |
| `postiAttivi` | `activeSeats` |  |
| `postiConfermati` | `confirmedSeats` |  |
| `postiLiberi` | `availableSeats` |  |
| `prenotazione` | `reservation` |  |
| `prenotazione":"` | `reservation":"` |  |
| `prenotazioni` | `reservations` |  |
| `prenotazioniNonConfermate` | `unconfirmedReservations` |  |
| `prenotazioniOggi` | `reservationsToday` |  |
| `prenotazioniPU` | `reservationsPU` |  |
| `prenotazionidb` | `reservationsdb` |  |
| `promemoriaInviato` | `reminderSent` |  |
| `registra` | `register` |  |
| `registraUser` | `registerUser` |  |
| `registrazione` | `register` |  |
| `registro` | `registry` |  |
| `registroPrenotazioni` | `reservationRegistry` |  |
| `registroSale` | `roomRegistry` |  |
| `registroUtenti` | `userRegistry` |  |
| `reminderInviato` | `reminderSent` |  |
| `reminder_inviato` | `reminder_sent` |  |
| `reservationsSala` | `roomReservations` |  |
| `richiediRuolo` | `requireRole` |  |
| `richiesta` | `request` |  |
| `richiestaCreazione` | `creationRequest` |  |
| `riepilogo` | `summary` |  |
| `riepilogoAree` | `areaSummary` |  |
| `risolviFascia` | `resolveTimeSlot` |  |
| `risolviSala` | `resolveRoom` |  |
| `risolviStudent` | `resolveStudent` |  |
| `risultato` | `result` |  |
| `ruolo` | `role` |  |
| `sala` | `room` |  |
| `saleDisponibili` | `availableRooms` |  |
| `salva` | `save` |  |
| `salvaReservation` | `saveReservation` |  |
| `salvaSala` | `saveRoom` |  |
| `salvaTutti` | `saveAll` |  |
| `salvaUtente` | `saveUser` |  |
| `scrollPosti` | `seatScrollPane` |  |
| `seatCountsDisponibili` | `availableSeatCount` |  |
| `seatsAssegnate` | `assignedSeats` |  |
| `seatsDisponibili` | `availableSeats` |  |
| `selectDataSalaPane` | `dateRoomSelectionPanel` |  |
| `selectDettaglioSala` | `getRoomDetail` |  |
| `seleziona` | `select` |  |
| `servizioNotifiche` | `notificationService` |  |
| `setCodiceIdentificativoInterno` | `setInternalIdentifierCode` |  |
| `setCognome` | `setSurname` |  |
| `setDescrizione` | `setDescription` |  |
| `setDisponibile` | `setAvailable` |  |
| `setEtichetta` | `setLabel` |  |
| `setEtichettaFascia` | `setTimeSlotLabel` |  |
| `setFasceOrarie` | `setTimeSlots` |  |
| `setIdFascia` | `setTimeSlotId` |  |
| `setIdPostazione` | `setSeatId` |  |
| `setIdSala` | `setRoomId` |  |
| `setIdStudent` | `setStudentId` |  |
| `setIdStudente` | `setStudentId` |  |
| `setIdentificativo` | `setIdentifier` |  |
| `setMatricola` | `setStudentNumber` |  |
| `setNome` | `setName` |  |
| `setNomeSala` | `setRoomName` |  |
| `setNumero` | `setNumber` |  |
| `setNumeroPostazioni` | `setSeatCount` |  |
| `setNumeroPostazioniTotali` | `setTotalSeatCount` |  |
| `setNumeroTotaleAccessi` | `setTotalVisitCount` |  |
| `setOrariApertura` | `setOpeningTimes` |  |
| `setOrariChiusura` | `setClosingTimes` |  |
| `setPostazioni` | `setSeats` |  |
| `setPostazioniAree` | `setAreaSeatCounts` |  |
| `setPostiAttivi` | `setActiveSeats` |  |
| `setPostiConfermati` | `setConfirmedSeats` |  |
| `setPostiDisponibili` | `setAvailableSeatCount` |  |
| `setPostiLiberi` | `setAvailableSeats` |  |
| `setPrenotazioniNonConfermate` | `setUnconfirmedReservations` |  |
| `setPrenotazioniOggi` | `setReservationsToday` |  |
| `setPromemoriaInviato` | `setReminderSent` |  |
| `setRuolo` | `setRole` |  |
| `setTipologia` | `setType` |  |
| `setTipologiaArea` | `setAreaType` |  |
| `setTipologie` | `setTypes` |  |
| `slotGiorno` | `daySlots` |  |
| `slotOrario` | `timeSlots` |  |
| `spinPostazioni` | `seatSpinner` |  |
| `strategiaAssegnazione` | `assignmentStrategy` |  |
| `studente` | `student` |  |
| `surnameLungo` | `longSurname` |  |
| `timeDelGiorno` | `dayWorkingHours` |  |
| `timeSlotOraria` | `timeSlot` |  |
| `timeSlot_oraria_id` | `time_slot_id` |  |
| `tipologia` | `type` |  |
| `tipologie` | `types` |  |
| `titleLabelSala` | `roomTitleLabel` |  |
| `trovaAreaPerId` | `findAreaById` |  |
| `trovaFasciaPerId` | `findTimeSlotById` |  |
| `trovaPerId` | `findById` |  |
| `trovaSeatPerId` | `findSeatById` |  |
| `trovaStudentPerId` | `findStudentById` |  |
| `trovate` | `found` |  |
| `txtAperturaGiovedi` | `thursdayOpeningField` |  |
| `txtAperturaLunedi` | `mondayOpeningField` |  |
| `txtAperturaMartedi` | `tuesdayOpeningField` |  |
| `txtAperturaMercoledi` | `wednesdayOpeningField` |  |
| `txtAperturaVenerdi` | `fridayOpeningField` |  |
| `txtChiusuraGiovedi` | `thursdayClosingField` |  |
| `txtChiusuraLunedi` | `mondayClosingField` |  |
| `txtChiusuraMartedi` | `tuesdayClosingField` |  |
| `txtChiusuraMercoledi` | `wednesdayClosingField` |  |
| `txtChiusuraVenerdi` | `fridayClosingField` |  |
| `txtDescrizione` | `descriptionField` |  |
| `utente` | `user` |  |
| `validaEmail` | `validateEmail` |  |
| `validaIdentificativo` | `validateIdentifier` |  |
| `validaNomeCogname` | `validateNameAndSurname` |  |
| `verificaCorrettezzaLibrarian` | `validateLibrarian` |  |
| `verificaCorrettezzaStudent` | `validateStudent` |  |
| `verificaCredenziali` | `verifyCredentials` |  |
| `verificaDataConsultabile` | `validateQueryDate` |  |
| `verificaDataInGiorniApertura` | `isOpenOnDate` |  |
| `verificaDisponibilita` | `isAvailable` |  |
| `verificaFormatoCredenziali` | `validateCredentialFormat` |  |
| `verificaIntervalloAnnullamentoReservation` | `validateCancellationWindow` |  |
| `verificaNumeroPostazioni` | `validateSeatCount` |  |
| `verificaProprieta` | `validateOwnership` |  |
| `verificaReservationAttivaInDataCorrente` | `validateActiveReservationForCurrentDate` |  |
| `verificaReservationAttivaOConfermataInDataFascia` | `hasActiveOrConfirmedReservationForDateAndSlot` |  |
| `verificaRuolo` | `isValidRole` |  |
| `verificaSeatInArea` | `validateSeatInArea` |  |
| `verificaUnicita` | `validateUniqueness` |  |
| `verificaValidita` | `validate` |  |
| `verificaValiditaDati` | `validateData` |  |
| `verificaValiditaListeOrari` | `validateWorkingHourLists` |  |

## Json Api

| Italian | English | Notes |
|---|---|---|
| `cognome` | `surname` |  |
| `descrizione` | `description` |  |
| `granaMinuti` | `slotDurationMinutes` |  |
| `idArea` | `areaId` |  |
| `idFascia` | `timeSlotId` |  |
| `idPostazione` | `seatId` |  |
| `idPrenotazione` | `reservationId` |  |
| `idSala` | `roomId` |  |
| `idSalaStudio` | `studyRoomId` |  |
| `idStudente` | `studentId` |  |
| `identificativo` | `identifier` |  |
| `nome` | `name` |  |
| `numeroPostazioni` | `seatCount` |  |
| `orariApertura` | `openingTimes` |  |
| `orariChiusura` | `closingTimes` |  |
| `postazioniAree` | `areaSeatCounts` |  |
| `ruolo` | `role` |  |
| `stato` | `status` |  |
| `tipologie` | `types` |  |

## Maven

| Italian | English | Notes |
|---|---|---|
| `GestioneBiblioteca` | `library-reservation-system` |  |

## Package

| Italian | English | Notes |
|---|---|---|
| `it.unina.prenotazioni` | `it.unina.reservations` |  |

## Route

| Italian | English | Notes |
|---|---|---|
| `/annulla` | `/cancel` |  |
| `/api/monitoraggio` | `/api/monitoring` |  |
| `/api/prenotazioni` | `/api/reservations` |  |
| `/api/sale` | `/api/rooms` |  |
| `/api/studente` | `/api/student` |  |
| `/dettaglio` | `/detail` |  |
| `/disponibili` | `/available` |  |
| `/effettua` | `/create` |  |
| `/fasce` | `/time-slots` |  |
| `/profilo` | `/profile` |  |
| `/registrazione` | `/register` |  |
| `/statistiche` | `/statistics` |  |
| `/storico` | `/history` |  |
| `/{idPrenotazione}/annulla` | `/{reservationId}/cancel` |  |
| `/{idPrenotazione}/checkin` | `/{reservationId}/checkIn` |  |

## Value

| Italian | English | Notes |
|---|---|---|
| `ANNULLATA` | `CANCELLED` |  |
| `ATTIVA` | `ACTIVE` |  |
| `BIBLIOTECARIO` | `LIBRARIAN` |  |
| `CONCLUSA` | `COMPLETED` |  |
| `CONFERMATA` | `CONFIRMED` |  |
| `SCADUTA` | `EXPIRED` |  |
| `STUDENTE` | `STUDENT` |  |
| `comune` | `common` |  |

## Web File

| Italian | English | Notes |
|---|---|---|
| `crea-sala.html` | `create-room.html` |  |
| `dashboard-bibliotecario.html` | `librarian-dashboard.html` |  |
| `dashboard-studente.html` | `student-dashboard.html` |  |
| `prenotazione.html` | `reservation.html` |  |
| `registrazione.html` | `registration.html` |  |
